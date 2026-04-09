#!/usr/bin/env osascript -l JavaScript

// Auto-approves Xcode MCP connection dialogs via UI automation.
// Based on: https://bleepingswift.com/blog/auto-approve-xcode-mcp-connection

function run() {
  const xcode = Application('Xcode')
  if (!xcode.running()) {
    return 'Xcode not running'
  }

  const systemEvents = Application('System Events')
  const xcodeProcess = systemEvents.processes.byName('Xcode')

  let approvedCount = 0

  try {
    const windows = xcodeProcess.windows()
    for (const window of windows) {
      // Look for dialog windows asking about MCP access
      const staticTexts = window.staticTexts()
      for (const text of staticTexts) {
        if (text.value().includes('to access Xcode?')) {
          // Find and click the Allow button
          const buttons = window.buttons()
          for (const button of buttons) {
            if (button.name() === 'Allow') {
              button.click()
              approvedCount++
              break
            }
          }
        }
      }
    }
  } catch (e) {
    return 'Error: ' + e.message
  }

  return approvedCount > 0
    ? `Approved ${approvedCount} MCP connection(s)`
    : 'No pending MCP dialogs'
}
