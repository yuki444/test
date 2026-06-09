import Foundation
import Combine

enum RhythmState {
    case idle
    case recording(secondsLeft: Double)
    case playing
}

struct RecordedTap {
    let buttonId: Int
    let timestamp: TimeInterval
    let frequency: Double
    let waveform: WaveformType
}

class RhythmViewModel: ObservableObject {
    @Published var state: RhythmState = .idle
    @Published var showPraise = false
    @Published var activeButtonId: Int? = nil
    @Published var characterBeat = false

    private let audioEngine: AudioEngine
    private var recordedTaps: [RecordedTap] = []
    private var recordingStartTime: TimeInterval = 0
    private var recordingTimer: Timer?
    private var playbackTimer: Timer?
    private var quantizedPattern: [(slot: Int, buttonId: Int, frequency: Double, waveform: WaveformType)] = []
    private var currentSlot = 0
    private var loopCount = 0
    private var hasShownPraise = false

    let recordingDuration: Double = 4.0
    let slotsPerMeasure = 16

    init(audioEngine: AudioEngine) {
        self.audioEngine = audioEngine
    }

    func startRecording(theme: Theme) {
        stopPlayback()
        recordedTaps = []
        hasShownPraise = false
        recordingStartTime = Date().timeIntervalSinceReferenceDate
        state = .recording(secondsLeft: recordingDuration)

        recordingTimer = Timer.scheduledTimer(withTimeInterval: 0.05, repeats: true) { [weak self] _ in
            guard let self else { return }
            let elapsed = Date().timeIntervalSinceReferenceDate - self.recordingStartTime
            let remaining = self.recordingDuration - elapsed
            if remaining <= 0 {
                self.finishRecording(theme: theme)
            } else {
                self.state = .recording(secondsLeft: remaining)
            }
        }
    }

    func tapButton(_ button: SoundButton, theme: Theme) {
        audioEngine.playNote(frequency: button.frequency, waveform: button.waveform)

        // Animate button flash
        activeButtonId = button.id
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
            self.activeButtonId = nil
        }

        if case .recording = state {
            let elapsed = Date().timeIntervalSinceReferenceDate - recordingStartTime
            recordedTaps.append(RecordedTap(
                buttonId: button.id,
                timestamp: elapsed,
                frequency: button.frequency,
                waveform: button.waveform
            ))
        }
    }

    private func finishRecording(theme: Theme) {
        recordingTimer?.invalidate()
        recordingTimer = nil

        quantizedPattern = quantize(taps: recordedTaps, bpm: theme.bpm)

        if quantizedPattern.isEmpty {
            // No taps recorded – add a default beat so playback works
            let btn = theme.buttons[0]
            quantizedPattern = [(slot: 0, buttonId: btn.id, frequency: btn.frequency, waveform: btn.waveform),
                                 (slot: 8, buttonId: btn.id, frequency: btn.frequency, waveform: btn.waveform)]
        }

        startPlayback(theme: theme)
    }

    private func quantize(taps: [RecordedTap], bpm: Double) -> [(slot: Int, buttonId: Int, frequency: Double, waveform: WaveformType)] {
        let beatDuration = 60.0 / bpm
        let sixteenth = beatDuration / 4.0
        var slotMap: [Int: RecordedTap] = [:]

        for tap in taps {
            let raw = tap.timestamp / sixteenth
            let slot = Int(raw.rounded()) % slotsPerMeasure
            // Last tap wins per slot
            slotMap[slot] = tap
        }

        return slotMap.map { (slot: $0.key, buttonId: $0.value.buttonId, frequency: $0.value.frequency, waveform: $0.value.waveform) }
            .sorted { $0.slot < $1.slot }
    }

    private func startPlayback(theme: Theme) {
        state = .playing
        loopCount = 0
        currentSlot = 0

        let beatDuration = 60.0 / theme.bpm
        let sixteenth = beatDuration / 4.0

        playbackTimer = Timer.scheduledTimer(withTimeInterval: sixteenth, repeats: true) { [weak self] _ in
            guard let self else { return }
            self.tickPlayback()
        }
    }

    private func tickPlayback() {
        let hits = quantizedPattern.filter { $0.slot == currentSlot }
        for hit in hits {
            audioEngine.playNote(frequency: hit.frequency, waveform: hit.waveform)
            activeButtonId = hit.buttonId
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.12) {
                self.activeButtonId = nil
            }
        }

        // Character beat on every 4th slot
        if currentSlot % 4 == 0 {
            characterBeat = true
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                self.characterBeat = false
            }
        }

        currentSlot += 1
        if currentSlot >= slotsPerMeasure {
            currentSlot = 0
            loopCount += 1
            if loopCount == 1 && !hasShownPraise {
                hasShownPraise = true
                DispatchQueue.main.async {
                    self.showPraise = true
                }
            }
        }
    }

    func stopPlayback() {
        playbackTimer?.invalidate()
        playbackTimer = nil
        recordingTimer?.invalidate()
        recordingTimer = nil
        state = .idle
        currentSlot = 0
        loopCount = 0
    }

    func buildSavedRhythm(themeId: Int) -> SavedRhythm {
        let taps = quantizedPattern.map { RhythmTap(buttonId: $0.buttonId, slot: $0.slot) }
        return SavedRhythm(themeId: themeId, taps: taps)
    }

    func playSavedRhythm(_ rhythm: SavedRhythm, theme: Theme) {
        stopPlayback()
        quantizedPattern = rhythm.taps.compactMap { tap in
            guard let btn = theme.buttons.first(where: { $0.id == tap.buttonId }) else { return nil }
            return (slot: tap.slot, buttonId: tap.buttonId, frequency: btn.frequency, waveform: btn.waveform)
        }
        if !quantizedPattern.isEmpty {
            startPlayback(theme: theme)
        }
    }

    deinit {
        stopPlayback()
    }
}
