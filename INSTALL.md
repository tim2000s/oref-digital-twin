# Running your own copy

The oref digital twin is a static web page. Your own copy runs on GitHub Pages under your GitHub
account, at no cost, and nothing in it needs a server: the page fetches Nightscout from the
browser, and the analysis runs in the browser. Setting it up takes about ten minutes and needs a
GitHub account and nothing else.

## 1. Fork the repository

On this repository's GitHub page, choose **Fork** (top right), keep the name
`oref-digital-twin`, and create the fork. A fork of a public repository is public. The page holds
no data of anyone's, so that is safe: your token and your Nightscout data stay in the browser of
whoever is using the page.

## 2. Turn on Actions and Pages

GitHub disables workflows in a new fork until you allow them.

1. In your fork, open the **Actions** tab and choose **I understand my workflows, go ahead and
   enable them**.
2. Open **Settings > Pages**. Under **Build and deployment**, set **Source** to
   **GitHub Actions**.

## 3. Build and publish

In the **Actions** tab, choose **Deploy web to GitHub Pages** in the list on the left, then
**Run workflow** on the `main` branch. It takes about a minute. When it finishes, your copy is at

    https://{your-github-id}.github.io/oref-digital-twin/

where `{your-github-id}` is your GitHub username in lower case: a user called `JaneDoe` opens
`https://janedoe.github.io/oref-digital-twin/`. If you renamed the fork, the last part of the
address is the new name.

The run's summary shows the same address. From then on every push to `main` republishes it.

## 4. Check it

Open the address. The status line should read "Ready." within a few seconds. Enter a Nightscout
address and a read-only token, and choose **Analyse**.

The Nightscout site must have `cors` in its `ENABLE` setting, because the page fetches from it
directly. A Nightscout behind nginx with a short `proxy_read_timeout` can time out on large
fetches; the page retries and says so if it gives up. `web/README.md` has the detail.

## 5. The plain-language summary

Nothing to set up. The page offers the summary on any browser with WebGPU, and runs the model
(Llama 3.1 8B, through WebLLM) on the device of whoever is using it. The first use downloads
about 5 GB, which the browser keeps. The README describes what the model is given and how its
text is checked.

## Keeping your copy up to date

On your fork's main page, **Sync fork > Update branch** pulls in the latest changes, and the push
republishes the page.

## Running it on your own computer instead

    bash web/build.sh
    python3 -m http.server -d web 8000

then open http://localhost:8000. `build.sh` needs network access, since it fetches WebLLM and
checks it against a pinned digest. The summary works locally too, because browsers treat
`localhost` as a secure origin and allow WebGPU there.

## What it is, and is not

The page is advisory and read-only. It never writes to Nightscout, a pump or a loop, and it is not
medical advice. The settings tests have been checked in simulation and against a small number of
real setting changes, with the results in `validation/`. Read those before relying on any figure
it shows.

## Licence

GNU Affero General Public License v3.0 or later (`LICENSE`). A public fork satisfies its
requirement to offer the source of a modified copy to the people using it. Third-party notices for
the bundled engine and WebLLM are in `THIRD_PARTY_NOTICES.txt`; the Pages workflow publishes both files with
the site.
