# HeyBot: AI-Powered Security & Code Analysis

HeyBot is a comprehensive DevSecOps tool that automates security scanning and provides AI-generated summaries of code analysis for your GitHub repositories. It integrates Trivy and OWASP Dependency-Check for vulnerability scanning, uses DeepSeek AI for insightful summaries, and is deployed on Kubernetes (Minikube for local development) via Helm and ArgoCD, with a CI/CD pipeline powered by GitHub Actions.

---

## Prerequisites

Before you begin, ensure you have the following installed and configured:

*   **Docker Desktop:** With Kubernetes enabled. Alternatively, **Minikube** can be used.
*   **`kubectl`:** Command-line tool for Kubernetes.
*   **Node.js & `npm`:** For frontend development (latest LTS version recommended).
*   **Python:** For backend development (version 3.9+ recommended).
*   **Helm:** Package manager for Kubernetes.
*   **`git`:** For version control.
*   **(Optional) ArgoCD CLI:** For command-line interaction with ArgoCD.

---

## Project Structure

```
.
├── .github/workflows/        # GitHub Actions CI/CD pipeline
├── app/                      # FastAPI Backend & Scanning Logic
│   ├── .env.example          # Example environment variables for backend
│   ├── main.py               # Main application script (scanning, AI summary)
│   ├── api_server.py         # FastAPI server
│   ├── requirements.txt      # Python dependencies
│   └── model_humor.txt       # Text file for DeepSeek AI prompts
├── analysis/                 # Output directory for scan summaries (mounted on PV)
├── helm/heybot/              # Helm chart for HeyBot deployment
├── heybot_frontend/          # Next.js Frontend
│   ├── .env.local.example    # Example environment variables for frontend
│   └── package.json          # Node.js dependencies
├── k8s/                      # (Potentially) Kubernetes manifests (if not solely Helm)
├── argocd-app.yaml           # ArgoCD Application manifest for HeyBot
├── Dockerfile                # Dockerfile for the backend application
└── README.md                 # This file
```

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd heybot
```

### 2. Backend Setup (`app/`)

*   **Navigate to the backend directory:**
    ```bash
    cd app
    ```
*   **Create and activate a Python virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
*   **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
*   **Configure Environment Variables:**
    Create an `.env` file in the `app/` directory (you can copy `app/.env.example` if it exists).
    Populate it with the following:
    ```env
    DEEPSEEK_API_KEY="your_deepseek_api_key"
    MODEL_HUMOR_PATH="app/model_humor.txt" 
    # Add other backend-specific variables if any (e.g., Discord webhook URL)
    # DISCORD_WEBHOOK_URL="your_discord_webhook_url" 
    ```
    *   Ensure `model_humor.txt` exists in `app/`. This file contains prompts or context for the DeepSeek AI. Example content: `"Analyze the following security scan results and provide a concise, slightly humorous summary suitable for a Discord message."`

### 3. Frontend Setup (`heybot_frontend/`)

*   **Navigate to the frontend directory:**
    ```bash
    cd ../heybot_frontend  # Assuming you are in app/
    ```
*   **Install Node.js dependencies:**
    ```bash
    npm install
    ```
*   **Configure Environment Variables:**
    Create a `.env.local` file in the `heybot_frontend/` directory (you can copy `heybot_frontend/.env.local.example` if it exists).
    Populate it with your GitHub Personal Access Token (PAT) with `repo` scope:
    ```env
    NEXT_PUBLIC_GITHUB_TOKEN="your_github_pat"
    # For local development, if backend is in Minikube on a different port:
    NEXT_PUBLIC_API_BASE_URL="http://localhost:8081" 
    ```
    If running the backend locally (not in Minikube), `NEXT_PUBLIC_API_BASE_URL` might be `http://localhost:8000` (or your Uvicorn port).

---

## Local Development & Deployment

### 1. Start Minikube (if not using Docker Desktop Kubernetes)

```bash
minikube start --driver=docker --memory=4g --cpus=2 
minikube addons enable ingress # Optional, if using Ingress later
```
Ensure your `kubectl` context is pointing to Minikube: `kubectl config use-context minikube`.

### 2. Deploy ArgoCD (One-time setup)

*   **Create ArgoCD namespace:**
    ```bash
    kubectl create namespace argocd
    ```
*   **Install ArgoCD:**
    ```bash
    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    ```
*   **Access ArgoCD UI:**
    Wait for pods to be ready (`kubectl get pods -n argocd`). Then port-forward:
    ```bash
    kubectl port-forward svc/argocd-server -n argocd 8088:443
    ```
    Open `https://localhost:8088` in your browser (proceed if you see a certificate warning).
*   **Get ArgoCD Admin Password:**
    ```bash
    kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo
    ```
    Login to the ArgoCD UI with username `admin` and the retrieved password.

### 3. Deploy HeyBot using ArgoCD

*   From the root of the project, apply the HeyBot ArgoCD application manifest:
    ```bash
    kubectl apply -f argocd-app.yaml -n argocd 
    ```
    This tells ArgoCD to manage the HeyBot application based on the Helm chart in `helm/heybot/` and deploy it to the `default` namespace (or as configured in `argocd-app.yaml`).
*   ArgoCD will automatically sync and deploy HeyBot. You can monitor this in the ArgoCD UI.

### 4. Running the Backend Locally (Alternative for API dev)

*   Navigate to `app/`:
    ```bash
    cd app
    source venv/bin/activate 
    ```
*   Run Uvicorn server (ensure `.env` is configured):
    ```bash
    uvicorn api_server:app --reload --host 0.0.0.0 --port 8000 
    ```

### 5. Running the Frontend Locally

*   Navigate to `heybot_frontend/`:
    ```bash
    cd heybot_frontend
    ```
*   Start the Next.js development server (ensure `.env.local` is configured):
    ```bash
    npm run dev
    ```
    The frontend is typically accessible at `http://localhost:3000` or `http://localhost:3030`.

### 6. Connecting Frontend to Backend in Minikube

If the HeyBot backend is running in Minikube (deployed via Helm/ArgoCD), you need to port-forward the service:

*   Find the service name (usually `heybot` if your Helm release is named `heybot`):
    ```bash
    kubectl get svc -n default 
    ```
*   Port-forward the service:
    ```bash
    kubectl port-forward service/heybot 8081:80 -n default 
    ```
    (Assuming the service `heybot` exposes port `80` and you want to access it on local port `8081`).
*   Ensure your frontend's `NEXT_PUBLIC_API_BASE_URL` in `.env.local` is set to `http://localhost:8081`.

---

## Running Scans Manually

You can trigger scans for a specific commit directly using the Python script:

*   Navigate to the `app/` directory and activate your virtual environment.
*   Run the script:
    ```bash
    python main.py --mode scan --commit-id <your-commit-sha>
    ```
    This will:
    1.  Fetch the specified commit.
    2.  Run Trivy and OWASP Dependency-Check.
    3.  Send results to DeepSeek AI for summarization.
    4.  Save the summary and vulnerability counts to `analysis/<commit-id>_summary.json` and `analysis/latest_summary.json`.
    5.  (If configured) Send a message to Discord.

    The `analysis/` directory should be the one mounted as a Persistent Volume in your Kubernetes deployment so the API server can access these files.

---

## CI/CD Pipeline (GitHub Actions)

The `.github/workflows/main.yml` file defines the CI/CD pipeline:

1.  **On push to `main` or Pull Request to `main`:**
    *   Checks out the code.
    *   Sets up Python and Node.js.
    *   Runs linters/formatters (e.g., Black, Flake8, ESLint, Prettier - *if configured*).
    *   Runs backend tests (e.g., Pytest - *if configured*).
    *   Runs frontend tests (e.g., Jest, Cypress - *if configured*).
    *   **Runs the Python scan script (`python app/main.py --mode scan ...`)** to generate `_summary.json` files.
    *   Builds and pushes a Docker image for the backend to a container registry (e.g., Docker Hub, GitHub Container Registry).
    *   Updates the Kubernetes deployment by modifying the image tag in the Helm chart values (or directly patching the deployment) and relies on ArgoCD to pick up this change from the Git repository and re-deploy.

    **Important:** The CI pipeline needs secrets configured in GitHub repository settings (e.g., `DEEPSEEK_API_KEY`, `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `GH_TOKEN_FOR_CI_CD_ACTIONS`).

---

## Accessing the Application

*   **Frontend:** `http://localhost:3030` (or your npm dev port when running locally). If deployed via Ingress in Minikube, use the Minikube IP and Ingress path.
*   **Backend API (via port-forward):** `http://localhost:8081/security-analysis/latest` (or specific commit ID).
*   **ArgoCD UI:** `https://localhost:8088` (after port-forwarding).

---

## Troubleshooting

*   **Minikube IP/Port Issues:** Ensure Minikube is running and `kubectl` is configured correctly. Use `minikube ip` to get the IP if needed for Ingress.
*   **PVC Binding Problems:** Check `kubectl get pvc`, `kubectl describe pvc <pvc-name>`, and Minikube storage provisioner status. Ensure `analysis-pv` and `analysis-pvc` are correctly defined and bound.
*   **CORS Errors:** If the frontend cannot connect to the backend, check browser console for CORS errors. Ensure backend FastAPI CORS middleware is configured correctly and the frontend is calling the correct URL (especially with port-forwarding).
*   **API Key Setup:** Double-check that `DEEPSEEK_API_KEY` (backend `.env`) and `NEXT_PUBLIC_GITHUB_TOKEN` (frontend `.env.local`) are correctly set and accessible by the applications.
*   **ArgoCD Sync Failures:** Check logs in the ArgoCD UI for the HeyBot application to diagnose Helm chart issues or image pull errors.
*   **OWASP/Trivy Errors:** Ensure these tools are correctly installed in the Docker image and accessible. Check logs from the scan script.

---
This README provides a comprehensive guide to setting up, developing, deploying, and troubleshooting HeyBot.

```bash
kubectl apply -n argocd -f argocd-app.yaml
kubectl port-forward svc/argocd-server -n argocd 8088:443
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath='{.data.password}' | base64 -d
```

---
#### **2. Checkout repro and modify **
```bash
1. clone repo 
2. modify things for your repro
3. See a running pipeline
```

#### **3. Let's run **
```bash
1. go on heybot via shell
2. run command: python main.py
3. See your message in discord channel.
```
