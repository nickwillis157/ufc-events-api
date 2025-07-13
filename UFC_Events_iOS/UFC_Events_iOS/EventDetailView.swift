
import SwiftUI

struct EventDetailView: View {
    let event: UFCEvent
    @Environment(\.presentationMode) var presentationMode

    var body: some View {
        ZStack {
            Color.black.edgesIgnoringSafeArea(.all)

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    modalHeader

                    VStack(alignment: .leading, spacing: 15) {
                        Text("Fight Card")
                            .font(.title2)
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                            .padding(.horizontal)

                        segmentedFightCard
                    }
                }
            }
        }
        .navigationBarHidden(true)
    }

    private var modalHeader: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Button(action: {
                    presentationMode.wrappedValue.dismiss()
                }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.title)
                        .foregroundColor(Color(hex: "A0A0A0"))
                        .background(Color.black.opacity(0.5))
                        .clipShape(Circle())
                }
                Spacer()
            }
            .padding(.horizontal)
            .padding(.top, 20)

            Text(event.eventName)
                .font(.largeTitle)
                .fontWeight(.heavy)
                .foregroundStyle(
                    LinearGradient(
                        gradient: Gradient(colors: [Color(hex: "667eea"), Color(hex: "764ba2")]),
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .padding(.horizontal)

            Text("\(formatDate(event.eventDate)) • \(event.venue ?? "") \(event.location != nil ? "• \(event.location!)" : "")")
                .font(.subheadline)
                .foregroundColor(Color(hex: "A0A0A0"))
                .padding(.horizontal)
                .padding(.bottom, 20)
        }
        .background(
            Color.black.opacity(0.85)
                .background(.ultraThinMaterial)
                .edgesIgnoringSafeArea(.top)
                .overlay(
                    Rectangle()
                        .frame(height: 3)
                        .foregroundColor(Color(hex: "4facfe").opacity(0.8)),
                    alignment: .top
                )
        )
    }

    private var segmentedFightCard: some View {
        VStack(alignment: .leading, spacing: 20) {
            let sortedFights = event.fights.sorted(by: { $0.boutOrder > $1.boutOrder })
            let categorizedFights = categorizeFights(sortedFights)

            if !categorizedFights.mainCard.isEmpty {
                FightSegmentView(title: "Main Card", fights: categorizedFights.mainCard, totalFights: sortedFights.count, startIndex: categorizedFights.mainCardStartIndex)
            }
            if !categorizedFights.prelims.isEmpty {
                FightSegmentView(title: "Preliminary Card", fights: categorizedFights.prelims, totalFights: sortedFights.count, startIndex: categorizedFights.prelimsStartIndex)
            }
            if !categorizedFights.earlyPrelims.isEmpty {
                FightSegmentView(title: "Early Preliminary Card", fights: categorizedFights.earlyPrelims, totalFights: sortedFights.count, startIndex: categorizedFights.earlyPrelimsStartIndex)
            }
        }
        .padding(.horizontal)
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "MMMM d, yyyy"
        return formatter.string(from: date)
    }

    private func categorizeFights(_ sortedFights: [Fight]) -> (mainCard: [Fight], prelims: [Fight], earlyPrelims: [Fight], mainCardStartIndex: Int, prelimsStartIndex: Int, earlyPrelimsStartIndex: Int) {
        let totalFights = sortedFights.count

        // First try to use scraped segment data if available
        let scrapedSegments = groupByScrapedSegments(sortedFights)
        if scrapedSegments.hasSegmentData {
            var mainCard: [Fight] = []
            var prelims: [Fight] = []
            var earlyPrelims: [Fight] = []

            // Reconstruct order based on original sortedFights
            for fight in sortedFights {
                if fight.segment == .mainCard {
                    mainCard.append(fight)
                } else if fight.segment == .prelims {
                    prelims.append(fight)
                } else if fight.segment == .earlyPrelims {
                    earlyPrelims.append(fight)
                }
            }
            return (mainCard, prelims, earlyPrelims, 0, mainCard.count, mainCard.count + prelims.count)
        }

        // Fallback to intelligent categorization
        let fightAnalysis = analyzeFightImportance(sortedFights)

        var mainCardSize: Int
        var prelimsSize: Int
        var earlyPrelimsSize: Int

        if totalFights >= 11 {
            if totalFights == 11 {
                earlyPrelimsSize = 2
                prelimsSize = 5
                mainCardSize = 4
            } else if totalFights == 12 {
                earlyPrelimsSize = 3
                prelimsSize = 4
                mainCardSize = 5
            } else {
                earlyPrelimsSize = totalFights - 9
                prelimsSize = 4
                mainCardSize = 5
            }
        } else if totalFights >= 8 {
            earlyPrelimsSize = max(0, totalFights - 8)
            prelimsSize = min(4, totalFights - earlyPrelimsSize - 4)
            mainCardSize = totalFights - earlyPrelimsSize - prelimsSize
        } else {
            mainCardSize = totalFights
            prelimsSize = 0
            earlyPrelimsSize = 0
        }

        let adjustedSegments = adjustSegmentsByImportance(
            sortedFights, mainCardSize, prelimsSize, earlyPrelimsSize, fightAnalysis
        )

        return adjustedSegments
    }

    private func groupByScrapedSegments(_ fights: [Fight]) -> (mainCard: [Fight], prelims: [Fight], earlyPrelims: [Fight], hasSegmentData: Bool) {
        var mainCard: [Fight] = []
        var prelims: [Fight] = []
        var earlyPrelims: [Fight] = []
        var hasSegmentData = false

        for fight in fights {
            if let segment = fight.segment {
                hasSegmentData = true
                switch segment {
                case .mainCard:
                    mainCard.append(fight)
                case .prelims:
                    prelims.append(fight)
                case .earlyPrelims:
                    earlyPrelims.append(fight)
                }
            } else {
                // If any fight doesn't have segment data, we fall back to intelligent categorization
                hasSegmentData = false
                break
            }
        }
        return (mainCard, prelims, earlyPrelims, hasSegmentData)
    }

    private func analyzeFightImportance(_ sortedFights: [Fight]) -> [(fight: Fight, importance: Int, originalIndex: Int)] {
        return sortedFights.enumerated().map { (index, fight) in
            var importance = 0

            if index == 0 {
                importance += 100
            }

            if fight.titleFight != .none {
                importance += 50
            }

            let fighter1Name = fight.fighter1.name.lowercased()
            let fighter2Name = fight.fighter2.name.lowercased()

            let mainCardFighters = [
                "topuria", "oliveira", "pantoja", "royval", "dariush", "moicano",
                "talbott", "hermansson", "rodrigues", "cortez", "araujo",
                "mcgregor", "adesanya", "jones", "ngannou", "usman", "edwards",
                "poirier", "gaethje", "holloway", "volkanovski", "makhachev",
                "sterling", "cejudo", "figueiredo", "moreno", "shevchenko",
                "nunes", "zhang", "joanna", "rose", "rousey"
            ]

            for name in mainCardFighters {
                if fighter1Name.contains(name) || fighter2Name.contains(name) {
                    importance += 30
                    break
                }
            }

            let weightClass = fight.weightClass.lowercased()
            if weightClass.contains("championship") || weightClass.contains("title") {
                importance += 40
            }

            if weightClass.contains("women") {
                importance += 15
            }

            if weightClass.contains("heavyweight") {
                importance += 10
            }

            return (fight, importance, originalIndex: index)
        }
    }

    private func adjustSegmentsByImportance(
        _ sortedFights: [Fight],
        _ mainCardSize: Int,
        _ prelimsSize: Int,
        _ earlyPrelimsSize: Int,
        _ analysis: [(fight: Fight, importance: Int, originalIndex: Int)]
    ) -> (mainCard: [Fight], prelims: [Fight], earlyPrelims: [Fight], mainCardStartIndex: Int, prelimsStartIndex: Int, earlyPrelimsStartIndex: Int) {

        var currentMainCardSize = mainCardSize
        var currentPrelimsSize = prelimsSize

        let importanceSorted = analysis.sorted(by: { $0.importance > $1.importance })

        let highImportanceInPrelims = importanceSorted.prefix(mainCardSize + 2)
            .filter { $0.originalIndex >= mainCardSize }

        if !highImportanceInPrelims.isEmpty {
            currentMainCardSize = min(mainCardSize + 1, sortedFights.count - 2)
            currentPrelimsSize = max(0, prelimsSize - 1)
        }

        let mainCard = Array(sortedFights.prefix(currentMainCardSize))
        let prelims = Array(sortedFights.dropFirst(currentMainCardSize).prefix(currentPrelimsSize))
        let earlyPrelims = Array(sortedFights.dropFirst(currentMainCardSize + currentPrelimsSize))

        return (
            mainCard: mainCard,
            prelims: prelims,
            earlyPrelims: earlyPrelims,
            mainCardStartIndex: 0,
            prelimsStartIndex: mainCard.count,
            earlyPrelimsStartIndex: mainCard.count + prelims.count
        )
    }
}

struct EventDetailView_Previews: PreviewProvider {
    static var previews: some View {
        EventDetailView(event: UFCEvent.sampleData[0])
            .preferredColorScheme(.dark)
    }
}
