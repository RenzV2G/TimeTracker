<!-- Project Centered Logo -->
<div align="center">

<img src="images/timetracker_logo.png" width="215"/>

# Freelance Time Tracker

A lightweight and simple desktop application that automatically tracks work sessions and logs them to **Google Sheets** and monitor **Idle Detection**.


<a href="../../issues?q=is%3Aissue+label%3Abug">Report Bug</a>
· <a href="../../issues?q=is%3Aissue+label%3Aenhancement">Request Feature</a>

</div>


---
<br/>

<!-- Badges -->
<div align="center">

![Python](https://img.shields.io/badge/Python-3.14+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://github.com/RenzV2G/TimeTracker/blob/main/LICENSE)
[![Stargazers][stars-shield]][[stars-url](https://github.com/RenzV2G/TimeTracker/stargazers)]
![Downloads]([https://img.shields.io/github/downloads/RenzV2G/TimeTracker/total](https://github.com/RenzV2G/TimeTracker/releases/tag/v0.1.0))

</div>


## About The Project

Freelance Time Tracker is a simple **desktop time tracking application** designed for freelancers who want an easy way to track work hours and automatically store them in Google Sheets.

The application handles:

* Google authentication
* time tracking
* idle detection
* automatic logging to spreadsheets

## Early Development Notice

! This project is currently in **early development**.

Expect:

* minor bugs
* UI/UX improvements
* additional features
* performance optimizations

Feedback and contributions are welcome.

## Download

Download the latest release here:

https://github.com/YOUR_USERNAME/YOUR_REPOSITORY/releases

Download:

```
TimeTracker.exe
```

No installation required.

---

## Features

* Google account authentication
* Automatic logging to Google Sheets
* Client-based tracking
* Idle activity detection (3min/s inactivity detection)
* Real-time timer
* Simple desktop UI (Python TKinter)

---

## How To Use

### 1. Download the Application

Download the executable from the **Releases** or **Download Link**.

### 2. Run the Application

```
TimeTracker.exe
```

### 3. Sign In

A browser window will open requesting Google authentication.
DO NOTE!: The Application brand is not verified yet, you may encounter this.
![TimeTracker - signin](https://github.com/user-attachments/assets/820896f2-7730-40be-96a3-e6b1cb1109f5)

### 4. Enter Your Name

The application will ask for your display name.

### 5. Connect a Google Sheet

**Template - Google Sheet TimeTracker**

https://docs.google.com/spreadsheets/d/1m0kBAG3JPcJnCEeSIb0KvbC_pzOuar2JPM6QqbWzWxg/edit?usp=sharing

This is on "only view" link, duplicate this sheet to use it for your own and you may add a customization and add a separate cell for computation of total hours rendered

![TimeTracker - sheets](https://github.com/user-attachments/assets/58918715-44fc-4b34-a941-d1cc7195834f)


Paste your **Google Sheet URL**.

Example:

```
https://docs.google.com/spreadsheets/d/123456abcde/edit
```
! NOTE: if the sheet is not yours you may request the sheetURL with an editor access from the owner and use that link.

### 6. Select or Create a Client

Choose the client you want to track.

### 7. Start Tracking

Click **Clock In**.

### 8. End Session

Click **Clock Out**.

Your work session will automatically be recorded in your Google Sheet.

<p align="right">(<a href="#top">back to top</a>)</p>

---

## Developer Setup

Clone the repository:

```
git clone https://github.com/RenzV2G/TimeTracker.git
cd TimeTracker
```

Install dependencies:

```
pip install -r requirements.txt
```

Run the application:

```
python main.py
```

<p align="right">(<a href="#top">back to top</a>)</p>

---

## Google OAuth Setup (client_secret.json)

Before running the application, you must create OAuth credentials.

### 1. Create a Project

Go to Google Cloud Console and create a project.

### 2. Enable APIs

Enable:

* SpreadSheets
* openId
* userinfo.email

### 3. Create OAuth Credentials

Create **OAuth Client ID**.

Application type:

```
Desktop App
```

### 4. Download Credentials

Download the credentials JSON file.

Rename it:

```
client_secret.json
```

Place it in the root directory of the project.

<p align="right">(<a href="#top">back to top</a>)</p>

---

## Building the Executable

To build the application:

```
pyinstaller --onefile --windowed --clean --name TimeTracker --add-data "client_secret.json;." --add-data "sounds;sounds" --icon=timetracker.ico main.py
```

The executable will appear in:

```
dist/TimeTracker.exe
```

<p align="right">(<a href="#top">back to top</a>)</p>

---

## Project Structure

```
TimeTracker/
│
├── main.py
├── auth.py
├── config.py
├── constants.py
├── models.py
├── utils.py
│
├── frames/
│
├── sounds/
│
├── requirements.txt
├── README.md
└── LICENSE
```

---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Open a Pull Request to the Development branch

All pull requests are reviewed before merging.

---

## License

Distributed under the License, please read the LICENSE.txt for more information.

<p align="right">(<a href="#top">back to top</a>)</p>
