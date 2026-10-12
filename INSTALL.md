# Running your own copy

The oref digital twin is a static web page. Your own copy runs on GitHub Pages under your GitHub
account, at no cost, and nothing in it needs a server: the page fetches Nightscout from the
browser, and the analysis runs in the browser. Setting it up takes about ten minutes and needs a
GitHub account and nothing else.

## 1. Fork the repository

On https://github.com/tim2000s/oref-digital-twin, choose **Fork** (top right), keep the name
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

    https://<your-github-username>.github.io/oref-digital-twin/

The run's summary shows the same address. From then on every push to `main` republishes it.

## 4. Check it

Open the address. The status line should read "Ready." within a few seconds. Enter a Nightscout
address and a read-only token, and choose **Analyse**.

The Nightscout site must have `cors` in its `ENABLE` setting, because the page fetches from it
directly. A Nightscout behind nginx with a short `proxy_read_timeout` can time out on large
fetches; the page retries and says so if it gives up. `web/README.md` has the detail.

## 5. Optional: the written summary

The page can add a written summary of its findings, produced by a small language model on a
Cloudflare Worker that you run. Without one, the page leaves that option out and works fully.

1. Create a free Cloudflare account and enable Workers AI.
2. In your fork, edit `worker/wrangler.toml` and set `ALLOWED_ORIGIN` to
   `https://<your-github-username>.github.io` (no path after it).
3. Deploy the Worker from a computer with Node installed:

       cd worker
       npx wrangler login
       npx wrangler deploy

   It prints the Worker's address, ending `workers.dev`.
4. In your fork, open **Settings > Secrets and variables > Actions > Variables** and add a
   repository variable named `NARRATOR_URL` whose value is that address.
5. Run the **Deploy web to GitHub Pages** workflow again (step 3).

Only anonymous findings go to the Worker (percentages and the names of findings, never readings,
tokens or addresses), and the page checks the summary against the findings before showing it.
`worker/README.md` describes the rate limit and how to check it is bound.

## Keeping your copy up to date

On your fork's main page, **Sync fork > Update branch** pulls in the latest changes, and the push
republishes the page. A change you have made to `worker/wrangler.toml` may conflict; keep your own
`ALLOWED_ORIGIN`.

## Running it on your own computer instead

    bash web/build.sh
    python3 -m http.server -d web 8000

then open http://localhost:8000. The written summary is off in a local build.

## What it is, and is not

The page is advisory and read-only. It never writes to Nightscout, a pump or a loop, and it is not
medical advice. The settings tests have been checked in simulation and against a small number of
real setting changes, with the results in `validation/`. Read those before relying on any figure
it shows.

## Licence

See `LICENSE`.
