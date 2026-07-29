import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            AgendaView()
                .tabItem {
                    Label("Agenda", systemImage: "calendar")
                }

            ReminderListView()
                .tabItem {
                    Label("Rappels", systemImage: "checklist")
                }
        }
    }
}

#Preview {
    ContentView()
        .modelContainer(for: [EventItem.self, ReminderItem.self], inMemory: true)
}
