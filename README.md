# SQLPaf 
*SQL Penetration Assistant Framework*

![SQLPaf_Logo](https://github.com/user-attachments/assets/360c1632-a9f1-4740-b45b-f4b67027336a)

## ⚠️ Disclaimer
This tool is intended for authorized penetration testing and security research purposes only.
We are not responsible for any misuse or illegal activities.

## 📦 Requirements

- Python 3.10+
- SQLMap
- Gobuster
- gym
- selenium
- Pillow
- torch
- numpy

## ⚙️ Installation

Depending on your setup and how you prefer to run SQLPaf, there are two main installation methods available:

- Dockerized environment for a fast, isolated, and portable setup
- Local installation for direct execution on your machine

Both methods are simple to deploy. Below you'll find the detailed steps for each approach.

### 🐳 On Docker *(Recommendend)*

This method isolates SQLPaf and dependencies in a container, making deployment consistent across environments.

Clone the repository:

```bash
git clone https://github.com/your-repo/SQLPaf.git
cd SQLPaf
```

Build and launch the Docker:

```bash
docker build -t sqlpaf .
docker run -it --hostname pafologue --name SQLPaf sqlpaf
```

Run the code:

```bash
./SQLPaf.sh
```

### 💻 On your machine

If you are not familiar with Docker, you can still install it on your main machine.

Clone the repository:

```bash
git clone https://github.com/your-repo/SQLPaf.git
cd SQLPaf
```

Install python dependencies:

```bash
pip install -r requirements.txt
```

Give the code the authorisation of execution and run it:

```bash
chmod +x SQLPaf.sh
./SQLPaf.sh
```

## 👨‍💻 Authors :
 
- Vault-of-Jok3r - Léo Dardillac
- Zap2204 - Adrien Moncet
