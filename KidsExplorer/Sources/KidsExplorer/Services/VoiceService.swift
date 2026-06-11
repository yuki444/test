import AVFoundation

class VoiceService: NSObject, AVSpeechSynthesizerDelegate {
    static let shared = VoiceService()

    private let synthesizer = AVSpeechSynthesizer()
    var isEnabled: Bool = true
    var onSpeechFinished: (() -> Void)?

    private override init() {
        super.init()
        synthesizer.delegate = self
        configureAudioSession()
    }

    private func configureAudioSession() {
        try? AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio, options: .duckOthers)
        try? AVAudioSession.sharedInstance().setActive(true)
    }

    func speak(_ text: String, rate: Float = 0.42, pitch: Float = 1.15, completion: (() -> Void)? = nil) {
        guard isEnabled else {
            completion?()
            return
        }
        onSpeechFinished = completion
        synthesizer.stopSpeaking(at: .immediate)

        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "ja-JP")
        utterance.rate = rate
        utterance.pitchMultiplier = pitch
        utterance.volume = 1.0
        utterance.preUtteranceDelay = 0.2
        utterance.postUtteranceDelay = 0.3

        synthesizer.speak(utterance)
    }

    func stop() {
        synthesizer.stopSpeaking(at: .immediate)
    }

    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        DispatchQueue.main.async { [weak self] in
            self?.onSpeechFinished?()
            self?.onSpeechFinished = nil
        }
    }
}
