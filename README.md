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
├── k8s/                      # Kubernetes manifests
├── argocd-app.yaml           # ArgoCD Application manifest for HeyBot
├── Dockerfile                # Dockerfile for the backend application
└── README.md                 # This file
```

### 1. Initial Setup

*   **Clone Repository:**
    ```bash
    git clone
    ```
*   **Configure Backend (`app/.env`):**
    Copy `app/.env.example` to `app/.env` and set:
    ```env
    DEEPSEEK_API_KEY="your_deepseek_api_key"
    MODEL_HUMOR_PATH="app/model_humor.txt"
    DISCORD_WEBHOOK_URL="your_discord_webhook_url"
    NVD_API_KEY="your_nvd_api_key"
    ```

### 2. Start Minikube & Deploy ArgoCD (One-time)

*   **Start Minikube:**
    ```bash
    minikube start --driver=docker
    kubectl config use-context minikube
    ```
*   **Apply Kubernetes Base Manifests:**
    ```bash
    kubectl apply -f k8s
    ```
*   **Deploy ArgoCD:**
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

### 4. Accessing the Application

*   **Access Backend deployed in Minikube (via ArgoCD):**
    1.  Port-forward the HeyBot backend service (wait for the `heybot` service in `default` namespace:
    ```bash
    kubectl get svc -n default # Find your heybot service name, e.g., 'heybot'
    kubectl port-forward service/heybot 8081:80 -n default 
    ```
    2.  The API (running in Minikube) is now available at `http://localhost:8081`.

### 5. Running the Frontend Locally

*   Navigate to `heybot_frontend/`:
    ```bash
    cd heybot_frontend
    ```

*   Start the Next.js development server (ensure `.env.local` is configured):
    ```bash
    npm run dev
    ```
    Access the frontend, usually at `http://localhost:3000` or `http://localhost:3030`.

---

## CI/CD Pipeline (GitHub Actions)

The pipeline in `.github/workflows/main.yml`:
*   On push/PR to `main`:
    *   Builds and pushes the backend Docker image.
    *   Runs the scan script (`python app/main.py`) within a Docker container, using the just-built image. Results are stored in an artifact.
    *   Updates Kubernetes manifests via Helm, triggering ArgoCD to redeploy.
*   **Required Secrets:** Ensure `DEEPSEEK_API_KEY`, `NVD_API_KEY` (for OWASP), `DISCORD_WEBHOOK_URL`, `GHCR_TOKEN` (or equivalent for your registry), and `REPO_ACCESS_TOKEN` (if needed for checkout) are set in GitHub repository secrets.

---

## Local Backend Development (Without ArgoCD/Kubernetes)

1.  Navigate to `app/`, activate venv, install `requirements.txt`.
2.  Ensure `app/.env` is configured.
3.  Run Uvicorn:
    ```bash
    uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
    ```

---

## Troubleshooting Tips

*   **Minikube IP/Port:** Use `minikube ip` if needed.
*   **PVC Binding:** Check `kubectl get pvc,pv` and describe them for errors.
*   **CORS Errors:** Ensure backend FastAPI CORS is correctly configured for your frontend URL.
*   **ArgoCD Sync/Helm Issues:** Check logs in ArgoCD UI.
*   **Scan Errors:** Verify tool installations in `Dockerfile` and check script logs from CI or local runs. Ensure API keys are valid.

---

*This README provides a streamlined guide to get HeyBot up and running.*

```bash
kubectl apply -n argocd -f argocd-app.yaml
kubectl port-forward svc/argocd-server -n argocd 8088:443
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath='{.data.password}' | base64 -d
```

## Environment Variables & Secrets Configuration

To run HeyBot, you will need to configure several API keys and tokens. **Do not commit your secret files (`.env`, `.env.local`) to Git.**

### Local Development

1.  **Backend (`app/.env`):**
    Create this file from `app/.env.example`.
    *   `DEEPSEEK_API_KEY`: Your personal API key from DeepSeek.
    *   `MODEL_HUMOR_PATH`: Should be `app/model_humor.txt`.
    *   `DISCORD_WEBHOOK_URL`: Your Discord webhook URL for notifications.
    *   `NVD_API_KEY`: (Optional, for local scans) Your NVD API key for OWASP database updates.

### GitHub Actions CI/CD (Repository Secrets)

If you fork this repository and want to use the GitHub Actions pipeline, you need to configure the following secrets in your repository's `Settings > Secrets and variables > Actions`:

*   `DEEPSEEK_API_KEY`: Your DeepSeek API key.
*   `NVD_API_KEY`: Your NVD API key (highly recommended for OWASP scans).
*   `DISCORD_WEBHOOK_URL`: Your Discord webhook URL.
*   `GHCR_TOKEN`: A GitHub PAT with `write:packages` scope to push Docker images to your ghcr.io registry.
*   `REPO_ACCESS_TOKEN`: (Optional, usually needed if CI pushes to repo) A GitHub PAT with `repo` scope.
