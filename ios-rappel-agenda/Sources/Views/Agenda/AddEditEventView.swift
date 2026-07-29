import SwiftUI
import SwiftData

struct AddEditEventView: View {
    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss

    var event: EventItem?
    var initialDate: Date = Date()

    @State private var title: String = ""
    @State private var notes: String = ""
    @State private var startDate: Date = Date()
    @State private var endDate: Date = Date().addingTimeInterval(3600)
    @State private var isAllDay: Bool = false
    @State private var colorHex: String = "A3122E"

    private let colorOptions = ["A3122E", "1E6FD9", "2E9E5B", "C08A00", "6B3FA0"]

    var body: some View {
        NavigationStack {
            Form {
                Section("Détails") {
                    TextField("Titre", text: $title)
                    TextField("Notes", text: $notes, axis: .vertical)
                }

                Section("Date") {
                    Toggle("Toute la journée", isOn: $isAllDay)
                    DatePicker(
                        "Début",
                        selection: $startDate,
                        displayedComponents: isAllDay ? .date : [.date, .hourAndMinute]
                    )
                    DatePicker(
                        "Fin",
                        selection: $endDate,
                        in: startDate...,
                        displayedComponents: isAllDay ? .date : [.date, .hourAndMinute]
                    )
                }

                Section("Couleur") {
                    HStack {
                        ForEach(colorOptions, id: \.self) { hex in
                            Circle()
                                .fill(Color(hex: hex))
                                .frame(width: 28, height: 28)
                                .overlay(
                                    Circle().stroke(Color.primary, lineWidth: colorHex == hex ? 2 : 0)
                                )
                                .onTapGesture { colorHex = hex }
                        }
                    }
                }
            }
            .navigationTitle(event == nil ? "Nouvel événement" : "Modifier l'événement")
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
        if let event {
            title = event.title
            notes = event.notes
            startDate = event.startDate
            endDate = event.endDate
            isAllDay = event.isAllDay
            colorHex = event.colorHex
        } else {
            startDate = initialDate
            endDate = initialDate.addingTimeInterval(3600)
        }
    }

    private func save() {
        if let event {
            event.title = title
            event.notes = notes
            event.startDate = startDate
            event.endDate = endDate
            event.isAllDay = isAllDay
            event.colorHex = colorHex
        } else {
            let newEvent = EventItem(
                title: title,
                notes: notes,
                startDate: startDate,
                endDate: endDate,
                isAllDay: isAllDay,
                colorHex: colorHex
            )
            modelContext.insert(newEvent)
        }
        dismiss()
    }
}
