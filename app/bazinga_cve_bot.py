import logging
import json
import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Variables from the .env file
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
MODEL_HUMOR_PATH = os.getenv('MODEL_HUMOR_PATH1')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

if not DISCORD_WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL is missing in the .env file.")
if not MODEL_HUMOR_PATH:
    raise ValueError("MODEL_HUMOR_PATH1 is missing in the .env file.")
if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY is missing in the .env file.")

# Initialize DeepSeek client
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# Severity ranking for sorting
SEVERITY_ORDER = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
    "UNKNOWN": 4
}

def load_humor_template():
    """Load the Sheldon Cooper-style humor template"""
    try:
        with open(MODEL_HUMOR_PATH, 'r') as file:
            return file.read().strip()
    except Exception as e:
        logging.error(f"Error loading humor template: {e}")
        return """You are Sheldon Cooper from The Big Bang Theory, specializing in roasting vulnerabilities with Penny jokes. 
        Rules:
        - Always compare vulnerabilities to Penny's quirks
        - Include scientific references
        - Use signature phrases like "Bazinga!"
        - Keep jokes 1-2 sentences
        - Include emojis related to physics/science 🔭⚛️
        Example: "This buffer overflow is as unpredictable as Penny's acting career! Bazinga! 🎭"
        """

def sort_vulnerabilities(vulnerabilities):
    """Sort vulnerabilities by severity (CRITICAL > HIGH > MEDIUM > LOW)"""
    return sorted(
        vulnerabilities,
        key=lambda x: SEVERITY_ORDER.get(x.get('Severity', 'UNKNOWN'), 100)
    )

async def generate_security_report(vulnerabilities, humor_template):
    """Generate a full security report with joke, table, and action items using DeepSeek"""
    try:
        if not vulnerabilities:
            return "No vulnerabilities found! Your code is as flawless as Sheldon's rigid routine. Bazinga! ⚛️"

        # Sort vulnerabilities by severity before processing
        sorted_vulns = sort_vulnerabilities(vulnerabilities)

        prompt = f"""
        {humor_template}

        Analyze these vulnerabilities (sorted by severity) and generate:
        1. A Sheldon Cooper joke.
        2. A markdown table with columns: Package, Severity, CVE, Fixed Version, How to Fix.
        3. Key technical notes for critical/high vulnerabilities.
        4. Actionable remediation steps.

        Vulnerabilities (first 5 by severity):
        {json.dumps(sorted_vulns[:5], indent=2)}

        --- Example Format ---
        **Joke**: "This SQL injection is as messy as Penny's apartment! Bazinga! 🛋️"

        **Vulnerabilities**:
        ```
        | Package  | Severity | CVE              | Fixed Version | How to Fix                      |
        |----------|----------|------------------|---------------|---------------------------------|
        | libaom3  | CRITICAL | CVE-2023-6879    | Not specified | Upgrade via Debian security updates |
        |          | HIGH     | CVE-2023-39616   | Will not fix  | Monitor for future patches      |
        ```

        **Key Notes**:
        - libaom3: Heap overflow (CRITICAL) and memory read issue (HIGH).

        **Action**:
        - Patch CRITICAL issues immediately with `apt upgrade`.
        - Restrict untrusted inputs for HIGH-severity unfixable issues.
        """

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7  # Balance creativity and structure
        )
        
        report = response.choices[0].message.content
        if "Bazinga!" not in report:
            report = report.replace("\n", "\n") + " Bazinga! ⚛️"  # Ensure joke ending
        
        return report

    except Exception as e:
        logging.error(f"Error generating report: {e}")
        return "This vulnerability analysis failed harder than Penny's cooking! Bazinga! 🔥"

def load_trivy_logs(log_path="trivy_output.json"):
    try:
        with open(log_path, "r") as file:
            raw_data = json.load(file)
            vulnerabilities = []
            if isinstance(raw_data, dict):
                if "Results" in raw_data:
                    for result in raw_data["Results"]:
                        if "Vulnerabilities" in result:
                            vulnerabilities.extend(result["Vulnerabilities"])
                elif "vulnerabilities" in raw_data:
                    vulnerabilities = raw_data["vulnerabilities"]
            return vulnerabilities or []
    except Exception as e:
        logging.error(f"Error loading logs: {e}")
        return []

async def send_discord_message_async(message):
    try:
        payload = {"content": message}
        headers = {"Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers) as response:
                if response.status != 204:
                    logging.error(f"Discord responded with status: {response.status}")
    except Exception as e:
        logging.error(f"Error sending to Discord: {e}")

async def main():
    try:
        vulnerabilities = load_trivy_logs()
        humor_template = load_humor_template()
        
        report = await generate_security_report(vulnerabilities, humor_template)
        await send_discord_message_async(report)
        logging.info("Full security report sent to Discord")

    except Exception as e:
        logging.error(f"Error in main process: {e}")

if __name__ == "__main__":
    asyncio.run(main())