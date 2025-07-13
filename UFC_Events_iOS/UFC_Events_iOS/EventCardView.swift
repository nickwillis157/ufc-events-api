import SwiftUI

struct EventCardView: View {
    let event: UFCEvent
    @State private var isHovered = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header with title and status
            headerSection
            
            // Venue information
            venueSection
            
            // Main event section
            if let mainEvent = sortedFights.first {
                mainEventSection(mainEvent)
            }
            
            // Fight count
            fightCountSection
        }
        .padding(20)
        .background(cardBackground)
        .cornerRadius(20)
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(Color(hex: "303030"), lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.25), radius: 15, x: 0, y: 8)
        .scaleEffect(isHovered ? 1.02 : 1.0)
        .animation(.easeInOut(duration: 0.3), value: isHovered)
        .onHover { hovering in
            isHovered = hovering
        }
    }
    
    // MARK: - Computed Properties
    
    private var sortedFights: [Fight] {
        event.fights.sorted(by: { $0.boutOrder > $1.boutOrder })
    }
    
    private var isUpcoming: Bool {
        event.eventDate >= Date()
    }
    
    private var cardBackground: some View {
        RoundedRectangle(cornerRadius: 20)
            .fill(Color(hex: "1A1A1A").opacity(0.85))
            .background(.ultraThinMaterial)
    }
    
    // MARK: - Header Section
    
    private var headerSection: some View {
        HStack(alignment: .top, spacing: 15) {
            VStack(alignment: .leading, spacing: 8) {
                Text(event.eventName)
                    .font(.title2)
                    .fontWeight(.heavy)
                    .foregroundStyle(
                        LinearGradient(
                            gradient: Gradient(colors: [.white, Color(hex: "4facfe")]),
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .lineLimit(2)
                    .minimumScaleFactor(0.8)
                
                Text(formatDate(event.eventDate))
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundColor(Color(hex: "A0A0A0"))
                    .textCase(.uppercase)
            }
            
            Spacer()
            
            statusBadge
        }
        .padding(.bottom, 15)
    }
    
    private var statusBadge: some View {
        Text(event.status.displayName)
            .font(.caption)
            .fontWeight(.bold)
            .textCase(.uppercase)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(statusBackgroundColor)
            .foregroundColor(statusTextColor)
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(statusBorderColor, lineWidth: 1)
            )
    }
    
    private var statusBackgroundColor: Color {
        switch event.status {
        case .scheduled:
            return Color(hex: "28C76F").opacity(0.2)
        case .completed:
            return Color(hex: "4facfe").opacity(0.2)
        case .cancelled:
            return Color(hex: "FF4757").opacity(0.2)
        case .postponed:
            return Color(hex: "FFA726").opacity(0.2)
        }
    }
    
    private var statusTextColor: Color {
        switch event.status {
        case .scheduled:
            return Color(hex: "28C76F")
        case .completed:
            return Color(hex: "4facfe")
        case .cancelled:
            return Color(hex: "FF4757")
        case .postponed:
            return Color(hex: "FFA726")
        }
    }
    
    private var statusBorderColor: Color {
        statusTextColor
    }
    
    // MARK: - Venue Section
    
    private var venueSection: some View {
        HStack(spacing: 8) {
            Image(systemName: "mappin.circle.fill")
                .font(.subheadline)
                .foregroundColor(Color(hex: "A0A0A0"))
            
            Text(venueText)
                .font(.subheadline)
                .fontWeight(.medium)
                .foregroundColor(Color(hex: "A0A0A0"))
                .lineLimit(2)
        }
        .padding(.bottom, 20)
    }
    
    private var venueText: String {
        var text = event.venue ?? ""
        if let location = event.location {
            if !text.isEmpty {
                text += " • \(location)"
            } else {
                text = location
            }
        }
        return text
    }
    
    // MARK: - Main Event Section
    
    private func mainEventSection(_ mainEvent: Fight) -> some View {
        VStack(alignment: .leading, spacing: 15) {
            HStack {
                Text("Main Event")
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundColor(Color(hex: "667eea"))
                    .textCase(.uppercase)
                
                if mainEvent.titleFight != .none {
                    HStack(spacing: 4) {
                        Image(systemName: "crown.fill")
                            .font(.caption)
                            .foregroundColor(Color(hex: "FFA726"))
                        Text("Title Fight")
                            .font(.caption)
                            .fontWeight(.bold)
                            .foregroundColor(Color(hex: "FFA726"))
                    }
                }
            }
            
            // Fighters
            VStack(spacing: 12) {
                fighterView(mainEvent.fighter1, isWinner: mainEvent.winner == mainEvent.fighter1.name)
                
                Text("VS")
                    .font(.title2)
                    .fontWeight(.black)
                    .foregroundStyle(
                        LinearGradient(
                            gradient: Gradient(colors: [Color(hex: "667eea"), Color(hex: "764ba2")]),
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .shadow(color: Color(hex: "667eea").opacity(0.4), radius: 4, x: 0, y: 2)
                
                fighterView(mainEvent.fighter2, isWinner: mainEvent.winner == mainEvent.fighter2.name)
            }
            
            // Weight Class
            Text(mainEvent.weightClass)
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundColor(mainEvent.titleFight != .none ? Color(hex: "FFA726") : Color(hex: "A0A0A0"))
                .textCase(.uppercase)
                .frame(maxWidth: .infinity)
                .multilineTextAlignment(.center)
            
            // Fight Result (if completed)
            if let winner = mainEvent.winner, !isUpcoming {
                VStack(spacing: 6) {
                    Text("Winner: \(winner)")
                        .font(.subheadline)
                        .fontWeight(.bold)
                        .foregroundStyle(
                            LinearGradient(
                                gradient: Gradient(colors: [Color(hex: "81FBB8"), Color(hex: "28C76F")]),
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .textCase(.uppercase)
                    
                    if let method = mainEvent.method {
                        Text(method)
                            .font(.caption)
                            .foregroundColor(Color(hex: "A0A0A0"))
                    }
                }
                .padding(.vertical, 12)
                .frame(maxWidth: .infinity)
                .background(Color.black.opacity(0.15))
                .cornerRadius(10)
            }
        }
        .padding(20)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(Color(hex: "667eea").opacity(0.15))
                .background(.ultraThinMaterial)
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .stroke(Color(hex: "667eea"), lineWidth: 1)
                )
        )
        .padding(.bottom, 20)
    }
    
    private func fighterView(_ fighter: Fighter, isWinner: Bool) -> some View {
        VStack(spacing: 6) {
            Text(fighter.name)
                .font(.headline)
                .fontWeight(.bold)
                .foregroundColor(isWinner ? Color(hex: "28C76F") : .white)
                .multilineTextAlignment(.center)
                .lineLimit(2)
                .minimumScaleFactor(0.8)
            
            if let record = fighter.record {
                Text(record)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(Color(hex: "A0A0A0"))
                    .font(.system(.caption, design: .monospaced))
            }
            
            if let country = fighter.country {
                Text(country)
                    .font(.caption2)
                    .foregroundColor(Color(hex: "A0A0A0"))
            }
        }
        .frame(maxWidth: .infinity)
    }
    
    // MARK: - Fight Count Section
    
    private var fightCountSection: some View {
        Text("\(event.fights.count) fight\(event.fights.count == 1 ? "" : "s") on card")
            .font(.subheadline)
            .fontWeight(.medium)
            .foregroundColor(Color(hex: "A0A0A0"))
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(Color(hex: "1A1A1A").opacity(0.7))
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color(hex: "303030"), lineWidth: 1)
            )
    }
    
    // MARK: - Helper Methods
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "MMMM d, yyyy"
        return formatter.string(from: date)
    }
}

// MARK: - Preview
struct EventCardView_Previews: PreviewProvider {
    static var previews: some View {
        ScrollView {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 350), spacing: 20)], spacing: 20) {
                ForEach(UFCEvent.sampleData.prefix(3)) { event in
                    EventCardView(event: event)
                }
            }
            .padding()
        }
        .background(Color.black)
        .preferredColorScheme(.dark)
    }
}