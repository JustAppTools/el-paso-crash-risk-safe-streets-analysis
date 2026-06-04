# GitHub Pages Hosting

This project is configured to publish the interactive dashboard in `web/` using GitHub Actions and GitHub Pages.

## Public URL

After Pages is enabled and the deploy workflow succeeds, the dashboard should be available at:

```text
https://justapptools.github.io/el-paso-crash-risk-safe-streets-analysis/
```

## Enable Pages

If the first deploy does not automatically create the site:

1. Open the repository on GitHub.
2. Go to **Settings**.
3. Go to **Pages**.
4. Under **Build and deployment**, set **Source** to **GitHub Actions**.
5. Run the **Deploy dashboard to GitHub Pages** workflow again, or push another change to `main`.

## What Gets Published

Only the `web/` folder is uploaded as the Pages artifact. That means the hosted site opens directly to the interactive dashboard:

- `web/index.html`
- `web/styles.css`
- `web/app.js`

The dashboard fetches public ArcGIS REST layers at runtime. Raw crash records and local GIS downloads are not committed or published.

