"""
Slack notifier for doc_modifier pipeline.

Standalone usage (run locally after documents are generated):
    python3 src/slack_notifier.py

Programmatic usage from cli.py:
    from slack_notifier import notify_completion, notify_batch_completion
"""

import os, glob, requests
from dotenv import load_dotenv

load_dotenv()


def notify_completion(name: str, output_paths: list, drive_links: list = None):
    """Notify Slack for a single applicant's documents."""
    BOT_TOKEN  = os.environ["SLACK_BOT_TOKEN"]
    CHANNEL_ID = os.environ["INPUT_CHANNEL_ID"]

    file_lines = "\n".join(f"• `{os.path.basename(p)}`" for p in output_paths)
    drive_lines = (
        "\n".join(f"• <{link}|Open in Drive>" for link in drive_links)
        if drive_links else ""
    )

    text = (
        f":white_check_mark: Documents for *{name}* have been generated.\n"
        f"{file_lines}"
        + (f"\n\nGoogle Drive:\n{drive_lines}" if drive_lines else "")
    )

    _post(BOT_TOKEN, CHANNEL_ID, text)


def notify_batch_completion(output_dir: str = "output/"):
    """Notify Slack with all documents found in output_dir (standalone mode)."""
    BOT_TOKEN  = os.environ["SLACK_BOT_TOKEN"]
    CHANNEL_ID = os.environ["INPUT_CHANNEL_ID"]

    docx_files = sorted(glob.glob(os.path.join(output_dir, "*.docx")))
    if not docx_files:
        print("No documents found in", output_dir)
        return

    lines = []
    for docx in docx_files:
        base = os.path.splitext(os.path.basename(docx))[0]
        pdf  = os.path.join(output_dir, base + ".pdf")
        pdf_part = f" + `{os.path.basename(pdf)}`" if os.path.exists(pdf) else ""
        lines.append(f"• `{os.path.basename(docx)}`{pdf_part}")

    text = (
        f":white_check_mark: *Document generation complete* — "
        f"{len(docx_files)} document(s) created from Google Spreadsheet `sample_data`.\n\n"
        + "\n".join(lines)
        + f"\n\n_All files saved to `{output_dir}` on local machine._"
    )

    _post(BOT_TOKEN, CHANNEL_ID, text)


def _post(token: str, channel: str, text: str):
    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {token}"},
        json={"channel": channel, "text": text},
    )
    result = resp.json()
    if result.get("ok"):
        print(f"✅ Slack notified ({channel})")
    else:
        print(f"❌ Slack error: {result.get('error')}")


if __name__ == "__main__":
    notify_batch_completion(output_dir="output/")
