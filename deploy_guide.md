# How to Deploy your QR Label App

This guide explains how to:
1.  Upload your code to GitHub.
2.  Make your website LIVE (accessible to anyone) using GitHub Pages.

## Prerequisites
-   You must have **Git** installed.
-   You must have a **GitHub Account**.

## Step 1: Initialize Git (One Time)
Open your terminal in the new project folder (`C:\Users\sanke\Desktop\v2qrcode`) and run:

```bash
cd C:\Users\sanke\Desktop\v2qrcode
git init
git add .
git commit -m "Initial V2 Release"
```

## Step 2: Create Repo on GitHub
1.  Go to [github.com/new](https://github.com/new).
2.  Name your repository (e.g., `qrcode-label-printer`).
3.  Click **Create repository**.
4.  Copy the commands under "…or push an existing repository from the command line". It usually looks like this:
    ```bash
    git remote add origin https://github.com/YOUR_USERNAME/qrcode-label-printer.git
    git branch -M main
    git push -u origin main
    ```
5.  Run those commands in your terminal.

## Step 3: Go Live!
I have already configured the code for deployment. You just need to run:

```bash
npm run deploy
```

Wait a minute, then open your browser to:
`https://YOUR_USERNAME.github.io/qrcode-label-printer/`

## Future Updates
If you change code later, just run:
1.  `npm run deploy` (updates the live site)
2.  `git add .`
3.  `git commit -m "update"`
4.  `git push` (updates your code backup)
