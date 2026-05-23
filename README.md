# OASI

<p align="center">
  <img src="images/oasi31.png" alt="OASI Logo" width="600">
</p>

<p align="center">
  <strong>An advanced reconnaissance and web scanner script.</strong><br>
  Coded with ❤️ by <strong>Mata</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/MataGreek/oasi?style=flat-square" alt="Stars">
  <img src="https://img.shields.io/github/forks/MataGreek/oasi?style=flat-square" alt="Forks">
  <img src="https://img.shields.io/github/license/MataGreek/oasi?style=flat-square" alt="License">
</p>

---

## 🚀 Features

OASI comes packed with comprehensive information gathering and scanning capabilities:

### Core Reconnaissance
* **Host Verification:** Validates target availability and resolves `Host IP`.
* **Security Headers Check:** Analyzes HTTP response headers for security misconfigurations.
* **WAF Detection:** Detects Web Application Firewalls protecting the target.
* **CMS Scanning:** Identifies common Content Management Systems (WordPress, Joomla, etc.).
* **Robots & Sitemap Auditing:** Automatically checks for `robots.txt` and `sitemap.xml`.
* **DNS & Whois Lookup:** Fetches complete domain configuration and registration details.
* **Reverse IP Lookup:** Discovers other domains hosted on the same server IP.

### Advanced Scanning
* **Subdomain Scanner:** Discovers active subdomains mapping the attack surface.
* **Directory & Upload Check:** Scans for standard upload directories and exposed file paths.
* **Web Shell & Directory Scanner:** Custom wordlist-based fuzzing to expose hidden directories and backdoor shells.
* **Port Scanner:** Performs basic network port sweeps on the target host.

---

## 📦 Installation

Ensure you have Python 3.x installed on your machine, then run the following commands:

```bash
# Clone the repository
git clone [https://github.com/MataGreek/oasi.git](https://github.com/MataGreek/oasi.git)

# Navigate into the project folder
cd oasi/

# Install the required dependencies
pip3 install -r requirements.txt