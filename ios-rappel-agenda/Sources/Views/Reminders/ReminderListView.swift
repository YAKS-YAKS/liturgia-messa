import SwiftUI
import SwiftData

struct ReminderListView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \ReminderItem.dueDate) private var reminders: [ReminderItem]

    @State private var showingAddReminder = false
    @State private var reminderToEdit: ReminderItem?

    private var pendingReminders: [ReminderItem] { reminders.filter { !$0.isCompleted } }
    private var completedReminders: [ReminderItem] { reminders.filter { $0.isCompleted } }

    var body: some View {
        NavigationStack {
            List {
                Section("À faire") {
                    if pendingReminders.isEmpty {
                        Text("Aucun rappel en attente").foregroundStyle(.secondary)
                    }
                    ForEach(pendingReminders) { reminder in
                        ReminderRow(reminder: reminder, onToggle: { toggle(reminder) })
                            .contentShape(Rectangle())
                            .onTapGesture { reminderToEdit = reminder }
                    }
                    .onDelete { offsets in delete(pendingReminders, at: offsets) }
                }

                if !completedReminders.isEmpty {
                    Section("Terminés") {
                        ForEach(completedReminders) { reminder in
                            ReminderRow(reminder: reminder, onToggle: { toggle(reminder) })
                                .contentShape(Rectangle())
                                .onTapGesture { reminderToEdit = reminder }
                        }
                        .onDelete { offsets in delete(completedReminders, at: offsets) }
                    }
                }
            }
            .navigationTitle("Rappels")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showingAddReminder = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingAddReminder) {
                AddEditReminderView()
            }
            .sheet(item: $reminderToEdit) { reminder in
                AddEditReminderView(reminder: reminder)
            }
        }
    }

    private func toggle(_ reminder: ReminderItem) {
        reminder.isCompleted.toggle()
        if reminder.isCompleted {
            NotificationManager.shared.cancel(for: reminder)
        } else {
            NotificationManager.shared.schedule(for: reminder)
        }
    }

    private func delete(_ list: [ReminderItem], at offsets: IndexSet) {
        for index in offsets {
            let reminder = list[index]
            NotificationManager.shared.cancel(for: reminder)
            modelContext.delete(reminder)
        }
    }
}

private struct ReminderRow: View {
    let reminder: ReminderItem
    let onToggle: () -> Void

    var body: some View {
        HStack {
            Button(action: onToggle) {
                Image(systemName: reminder.isCompleted ? "checkmark.circle.fill" : "circle")
                    .foregroundStyle(reminder.isCompleted ? .green : .secondary)
                    .font(.title3)
            }
            .buttonStyle(.plain)

            VStack(alignment: .leading, spacing: 2) {
                Text(reminder.title)
                    .strikethrough(reminder.isCompleted)
                    .foregroundStyle(reminder.isCompleted ? .secondary : .primary)
                Text(reminder.dueDate.formatted(date: .abbreviated, time: .shortened))
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            PriorityBadge(priority: reminder.priority)
        }
        .padding(.vertical, 2)
    }
}

private struct PriorityBadge: View {
    let priority: Priority

    private var color: Color {
        switch priority {
        case .low: return .gray
        case .medium: return .orange
        case .high: return .red
        }
    }

    var body: some View {
        Text(priority.label)
            .font(.caption2)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(color.opacity(0.15))
            .foregroundStyle(color)
            .clipShape(Capsule())
    }
}
