import SwiftUI
import SwiftData

struct AgendaView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \EventItem.startDate) private var events: [EventItem]

    @State private var selectedDate = Date()
    @State private var showingAddEvent = false
    @State private var eventToEdit: EventItem?

    private var calendar: Calendar { Calendar.current }

    private var eventsForSelectedDay: [EventItem] {
        events.filter { calendar.isDate($0.startDate, inSameDayAs: selectedDate) }
    }

    private var daysWithEvents: Set<DateComponents> {
        Set(events.map { calendar.dateComponents([.year, .month, .day], from: $0.startDate) })
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                MonthCalendarView(selectedDate: $selectedDate, markedDays: daysWithEvents)
                    .padding(.horizontal)

                Divider().padding(.top, 8)

                List {
                    if eventsForSelectedDay.isEmpty {
                        Text("Aucun événement ce jour-là")
                            .foregroundStyle(.secondary)
                    } else {
                        ForEach(eventsForSelectedDay) { event in
                            Button {
                                eventToEdit = event
                            } label: {
                                EventRow(event: event)
                            }
                            .buttonStyle(.plain)
                        }
                        .onDelete(perform: deleteEvents)
                    }
                }
                .listStyle(.plain)
            }
            .navigationTitle("Agenda")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showingAddEvent = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingAddEvent) {
                AddEditEventView(initialDate: selectedDate)
            }
            .sheet(item: $eventToEdit) { event in
                AddEditEventView(event: event)
            }
        }
    }

    private func deleteEvents(at offsets: IndexSet) {
        let dayEvents = eventsForSelectedDay
        for index in offsets {
            modelContext.delete(dayEvents[index])
        }
    }
}

private struct EventRow: View {
    let event: EventItem

    var body: some View {
        HStack {
            Circle()
                .fill(Color(hex: event.colorHex))
                .frame(width: 10, height: 10)

            VStack(alignment: .leading) {
                Text(event.title).font(.headline)
                if event.isAllDay {
                    Text("Toute la journée")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                } else {
                    Text(event.startDate.formatted(date: .omitted, time: .shortened))
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .padding(.vertical, 4)
    }
}
