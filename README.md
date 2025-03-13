# SQLPaf

![Status](https://img.shields.io/badge/Status-Stable-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Docker](https://img.shields.io/badge/Docker-Supported-blue)
![Gobuster](https://img.shields.io/badge/Gobuster-Integrated-blue)
![SQLMap](https://img.shields.io/badge/SQLMap-Automated-red)

![SQLPaf_Logo](https://github.com/user-attachments/assets/360c1632-a9f1-4740-b45b-f4b67027336a)

SQLPaf is a powerful penetration testing framework designed to automate the detection and exploitation of SQL injection vulnerabilities.
It combines Gobuster's brute-force web directory scanning, an AI-powered form recognition engine, and SQLMap's proven payload injection capabilities. The result is a streamlined and efficient process for identifying, analyzing, and exploiting vulnerable web applications at scale.

## ⚠️ Disclaimer

SQLPaf is designed exclusively for ethical penetration testing and security research with explicit authorization from the target owner.
Any unauthorized use of this tool against systems where you do not have permission is strictly prohibited.
The developers take no responsibility for illegal use or any damages resulting from improper application.

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

## 🏆 Acknowledgements

- [SQLMap](https://github.com/sqlmapproject/sqlmap))
- [Gobuster](https://github.com/OJ/gobuster)
