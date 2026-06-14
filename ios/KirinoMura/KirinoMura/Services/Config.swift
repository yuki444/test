import Foundation

enum Config {
    // Claude API key — set via CLAUDE_API_KEY environment variable
    // or replace the empty string with your key for local testing.
    static var claudeAPIKey: String {
        ProcessInfo.processInfo.environment["CLAUDE_API_KEY"] ?? ""
    }
}
