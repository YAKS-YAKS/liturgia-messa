import SwiftUI

struct MonthCalendarView: View {
    @Binding var selectedDate: Date
    var markedDays: Set<DateComponents>

    @State private var displayedMonth: Date = Date()

    private let calendar = Calendar.current
    private let columns = Array(repeating: GridItem(.flexible()), count: 7)

    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Button {
                    changeMonth(by: -1)
                } label: {
                    Image(systemName: "chevron.left")
                }

                Spacer()

                Text(displayedMonth.formatted(.dateTime.month(.wide).year()))
                    .font(.headline)

                Spacer()

                Button {
                    changeMonth(by: 1)
                } label: {
                    Image(systemName: "chevron.right")
                }
            }

            HStack {
                ForEach(shortWeekdaySymbols, id: \.self) { symbol in
                    Text(symbol)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .frame(maxWidth: .infinity)
                }
            }

            LazyVGrid(columns: columns, spacing: 8) {
                ForEach(Array(daysInMonthGrid.enumerated()), id: \.offset) { _, day in
                    if let day {
                        DayCell(
                            date: day,
                            isSelected: calendar.isDate(day, inSameDayAs: selectedDate),
                            isToday: calendar.isDateInToday(day),
                            isMarked: markedDays.contains(
                                calendar.dateComponents([.year, .month, .day], from: day)
                            )
                        )
                        .onTapGesture {
                            selectedDate = day
                        }
                    } else {
                        Color.clear.frame(height: 36)
                    }
                }
            }
        }
        .onAppear {
            displayedMonth = selectedDate
        }
    }

    private var shortWeekdaySymbols: [String] {
        let symbols = calendar.shortStandaloneWeekdaySymbols
        let firstWeekday = calendar.firstWeekday - 1
        return Array(symbols[firstWeekday...] + symbols[..<firstWeekday])
    }

    private var daysInMonthGrid: [Date?] {
        guard let monthInterval = calendar.dateInterval(of: .month, for: displayedMonth),
              let range = calendar.range(of: .day, in: .month, for: displayedMonth) else {
            return []
        }

        let firstOfMonth = monthInterval.start
        let firstWeekdayOfMonth = calendar.component(.weekday, from: firstOfMonth)
        let leadingEmptyDays = (firstWeekdayOfMonth - calendar.firstWeekday + 7) % 7

        var days: [Date?] = Array(repeating: nil, count: leadingEmptyDays)

        for dayOffset in 0..<range.count {
            if let date = calendar.date(byAdding: .day, value: dayOffset, to: firstOfMonth) {
                days.append(date)
            }
        }

        while days.count % 7 != 0 {
            days.append(nil)
        }

        return days
    }

    private func changeMonth(by value: Int) {
        if let newMonth = calendar.date(byAdding: .month, value: value, to: displayedMonth) {
            displayedMonth = newMonth
        }
    }
}

private struct DayCell: View {
    let date: Date
    let isSelected: Bool
    let isToday: Bool
    let isMarked: Bool

    private let calendar = Calendar.current

    var body: some View {
        VStack(spacing: 4) {
            Text("\(calendar.component(.day, from: date))")
                .font(.subheadline)
                .fontWeight(isToday ? .bold : .regular)
                .frame(width: 32, height: 32)
                .background(isSelected ? Color.accentColor : Color.clear)
                .foregroundStyle(isSelected ? .white : (isToday ? Color.accentColor : .primary))
                .clipShape(Circle())

            Circle()
                .fill(isMarked ? Color.accentColor : Color.clear)
                .frame(width: 5, height: 5)
        }
        .frame(maxWidth: .infinity)
    }
}
