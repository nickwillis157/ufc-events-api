import Foundation

extension Foundation.Bundle {
    static let module: Bundle = {
        let mainPath = Bundle.main.bundleURL.appendingPathComponent("UFC_Events_iOS_UFC_Events_iOS.bundle").path
        let buildPath = "/Users/nick/UFC Scraper/UFC_Events_iOS/.build/arm64-apple-macosx/debug/UFC_Events_iOS_UFC_Events_iOS.bundle"

        let preferredBundle = Bundle(path: mainPath)

        guard let bundle = preferredBundle ?? Bundle(path: buildPath) else {
            // Users can write a function called fatalError themselves, we should be resilient against that.
            Swift.fatalError("could not load resource bundle: from \(mainPath) or \(buildPath)")
        }

        return bundle
    }()
}