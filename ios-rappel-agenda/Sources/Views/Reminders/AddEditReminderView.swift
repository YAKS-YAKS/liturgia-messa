import SwiftUI
import SwiftData

struct AddEditReminderView: View {
    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss

    var reminder: ReminderItem?

    @State private var title: String = ""
    @State private var notes: String = ""
    @State private var dueDate: Date = Date().addingTimeInterval(3600)
    @State private var priority: Priority = .medium

    var body: some View {
        NavigationStack {
            Form {
                Section("Détails") {
                    TextField("Titre", text: $title)
                    TextField("Notes", text: $notes, axis: .vertical)
                }

                Section("Échéance") {
                    DatePicker("Date et heure", selection: $dueDate, displayedComponents: [.date, .hourAndMinute])
                }

                Section("Priorité") {
                    Picker("Priorité", selection: $priority) {
                        ForEach(Priority.allCases) { p in
                            Text(p.label).tag(p)
                        }
                    }
                    .pickerStyle(.segmented)
                }
            }
            .navigationTitle(reminder == nil ? "Nouveau rappel" : "Modifier le rappel")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Annuler") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Enregistrer") { save() }
                        .disabled(title.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
            .onAppear(perform: loadInitialValues)
        }
    }

    private func loadInitialValues() {
        if let reminder {
            title = reminder.title
            notes = reminder.notes
            dueDate = reminder.dueDate
            priority = reminder.priority
        }
    }

    private func save() {
        if let reminder {
            reminder.title = title
            reminder.notes = notes
            reminder.dueDate = dueDate
            reminder.priority = priority
            NotificationManager.shared.schedule(for: reminder)
        } else {
            let newReminder = ReminderItem(title: title, notes: notes, dueDate: dueDate, priority: priority)
            modelContext.insert(newReminder)
            NotificationManager.shared.schedule(for: newReminder)
        }
        dismiss()
    }
}
