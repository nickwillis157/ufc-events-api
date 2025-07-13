import SwiftUI

struct FightSegmentView: View {
    let title: String
    let fights: [Fight]
    let totalFights: Int
    let startIndex: Int
    
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            segmentHeader
            
            VStack(spacing: 15) {
                ForEach(Array(fights.enumerated()), id: \.element.id) { index, fight in
                    FightCardView(
                        fight: fight,
                        displayIndex: startIndex + index,
                        totalFights: totalFights,
                        isMainEvent: (startIndex + index) == 0
                    )
                }
            }
        }
    }
    
    private var segmentHeader: some View {
        HStack {
            Text(title)
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(segmentColor)
                .textCase(.uppercase)
            
            Spacer()
            
            Image(systemName: "antenna.radiowaves.left.and.right")
                .font(.caption)
                .foregroundColor(segmentColor.opacity(0.7))
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 15)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(segmentColor.opacity(0.15))
                .background(.ultraThinMaterial)
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .stroke(segmentColor, lineWidth: 1)
                )
                .overlay(
                    Rectangle()
                        .frame(height: 2)
                        .foregroundColor(segmentColor)
                        .opacity(0.7),
                    alignment: .top
                )
        )
        .shadow(color: segmentColor.opacity(0.25), radius: 8, x: 0, y: 4)
    }
    
    private var segmentColor: Color {
        switch title {
        case "Main Card":
            return Color(hex: "667eea")
        case "Preliminary Card":
            return Color(hex: "4facfe")
        case "Early Preliminary Card":
            return Color(hex: "28C76F")
        default:
            return Color(hex: "4facfe")
        }
    }
}

struct FightCardView: View {
    let fight: Fight
    let displayIndex: Int
    let totalFights: Int
    let isMainEvent: Bool
    
    var body: some View {
        VStack(alignment: .leading, spacing: 15) {
            fightOrderHeader
            
            fightersSection
            
            weightClassSection
            
            if let winner = fight.winner, !isUpcoming {
                resultSection(winner: winner)
            }
        }
        .padding(20)
        .background(cardBackground)
        .cornerRadius(16)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(isMainEvent ? Color(hex: "667eea") : Color(hex: "303030"), lineWidth: 1)
        )
        .shadow(
            color: isMainEvent ? Color(hex: "667eea").opacity(0.25) : Color.black.opacity(0.15),
            radius: isMainEvent ? 12 : 8,
            x: 0,
            y: isMainEvent ? 6 : 4
        )
    }
    
    private var cardBackground: some View {
        RoundedRectangle(cornerRadius: 16)
            .fill(isMainEvent ? Color(hex: "667eea").opacity(0.15) : Color(hex: "1A1A1A").opacity(0.7))
            .background(.ultraThinMaterial)
    }
    
    private var fightOrderHeader: some View {
        HStack {
            Text(boutLabel)
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(Color(hex: "A0A0A0"))
                .textCase(.uppercase)
            
            Spacer()
            
            if fight.titleFight != .none {
                HStack(spacing: 4) {
                    Image(systemName: "crown.fill")
                        .font(.caption)
                        .foregroundColor(Color(hex: "FFA726"))
                    Text("Title Fight")
                        .font(.caption)
                        .fontWeight(.bold)
                        .foregroundColor(Color(hex: "FFA726"))
                        .textCase(.uppercase)
                }
            }
        }
    }
    
    private var boutLabel: String {
        if isMainEvent {
            return "Main Event"
        } else if displayIndex == 1 {
            return "Co-Main Event"
        } else {
            let boutNumber = totalFights - displayIndex
            return "Bout \(boutNumber)"
        }
    }
    
    private var fightersSection: some View {
        VStack(spacing: 12) {
            fighterView(fight.fighter1, isWinner: fight.winner == fight.fighter1.name)
            
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
            
            fighterView(fight.fighter2, isWinner: fight.winner == fight.fighter2.name)
        }
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
    
    private var weightClassSection: some View {
        Text(fight.weightClass)
            .font(.subheadline)
            .fontWeight(.semibold)
            .foregroundColor(fight.titleFight != .none ? Color(hex: "FFA726") : Color(hex: "A0A0A0"))
            .textCase(.uppercase)
            .frame(maxWidth: .infinity)
            .multilineTextAlignment(.center)
    }
    
    private func resultSection(winner: String) -> some View {
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
            
            if let method = fight.method {
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
    
    private var isUpcoming: Bool {
        fight.winner == nil
    }
}

// MARK: - Preview
struct FightSegmentView_Previews: PreviewProvider {
    static var previews: some View {
        ScrollView {
            VStack(spacing: 20) {
                if let sampleEvent = UFCEvent.sampleData.first {
                    let sortedFights = sampleEvent.fights.sorted(by: { $0.boutOrder > $1.boutOrder })
                    FightSegmentView(
                        title: "Main Card",
                        fights: Array(sortedFights.prefix(2)),
                        totalFights: sortedFights.count,
                        startIndex: 0
                    )
                }
            }
            .padding()
        }
        .background(Color.black)
        .preferredColorScheme(.dark)
    }
}