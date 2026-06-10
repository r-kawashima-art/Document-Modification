const CHANNEL_IDS = [
  "C0B6Z2AHUTB", // #channel-one
  // "C0B6TLECG8M",
];
const APPROVER_ID = "U0AR3UR5C5S"; // approver's Member ID

function getSlackBotToken() {
  const token = PropertiesService.getScriptProperties().getProperty("SLACK_BOT_TOKEN");
  if (!token) {
    throw new Error("Missing SLACK_BOT_TOKEN in Apps Script script properties.");
  }
  return token;
}

function requestApproval(e) {
  // 2. Get the active sheet and the range that was just edited
  const sheet = e.source.getActiveSheet();
  const range = e.range;
  const row = range.getRow();
  
  // OPTIONAL: Only run if a specific sheet is edited (e.g., "Sheet1")
  if (sheet.getName() !== "Sheet1") return;
  
  // 3. Check if the edit happened in a new row 
  // (This triggers if the edit is on the last row or if data is appended)
  if (row === sheet.getLastRow()) {
    const range = e.range;
    const sheet = range.getSheet();
    const spreadsheet = e.source || SpreadsheetApp.getActiveSpreadsheet();

    const message = [
      `<@${APPROVER_ID}> Approval request`,
      `Spreadsheet: ${spreadsheet.getName()}`,
      `Sheet: ${sheet.getName()}`,
      `Edited range: ${range.getA1Notation()}`,
    ].join("\n");

    CHANNEL_IDS.forEach((channelId) => {
      UrlFetchApp.fetch("https://slack.com/api/chat.postMessage", {
        method: "post",
        contentType: "application/json",
        headers: { Authorization: `Bearer ${getSlackBotToken()}` },
        payload: JSON.stringify({
          channel: channelId,
          text: message,
          blocks: [
            {
              type: "section",
              text: {
                type: "mrkdwn",
                text: message,
              },
            },
            {
              type: "actions",
              elements: [
                {
                  type: "workflow_button",
                  text: { type: "plain_text", text: "✅ Approve" },
                  style: "primary",
                  workflow: {
                    trigger: {
                      url: "https://slack.com/shortcuts/YOUR_WORKFLOW_TRIGGER_URL",
                      customizable_input_parameters: [
                        { name: "status", value: "approved" },
                        { name: "sheet_name", value: sheet.getName() },
                        { name: "range", value: range.getA1Notation() },
                      ],
                    },
                  },
                },
                {
                  type: "workflow_button",
                  text: { type: "plain_text", text: "❌ Reject" },
                  style: "danger",
                  workflow: {
                    trigger: {
                      url: "https://slack.com/shortcuts/YOUR_WORKFLOW_TRIGGER_URL",
                      customizable_input_parameters: [
                        { name: "status", value: "rejected" },
                        { name: "sheet_name", value: sheet.getName() },
                        { name: "range", value: range.getA1Notation() },
                      ],
                    },
                  },
                },
              ],
            },
          ],
        }),
      });
    });
  }
}
