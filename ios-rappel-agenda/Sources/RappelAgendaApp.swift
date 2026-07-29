import SwiftUI
import SwiftData

@main
struct RappelAgendaApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .onAppear {
                    NotificationManager.shared.requestAuthorizationIfNeeded()
                }
        }
        .modelContainer(for: [EventItem.self, ReminderItem.self])
    }
}
