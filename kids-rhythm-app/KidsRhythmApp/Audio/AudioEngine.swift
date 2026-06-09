import AVFoundation
import Foundation

class AudioEngine: ObservableObject {
    private let engine = AVAudioEngine()
    private var playerNodes: [AVAudioPlayerNode] = []
    private var nodeIndex = 0
    private let poolSize = 8
    private var audioFormat: AVAudioFormat?

    init() {
        setupSession()
        setupEngine()
    }

    private func setupSession() {
        let session = AVAudioSession.sharedInstance()
        try? session.setCategory(.playback, mode: .default)
        try? session.setActive(true)
    }

    private func setupEngine() {
        let sampleRate: Double = 44100
        guard let format = AVAudioFormat(standardFormatWithSampleRate: sampleRate, channels: 1) else { return }
        audioFormat = format

        for _ in 0..<poolSize {
            let node = AVAudioPlayerNode()
            engine.attach(node)
            engine.connect(node, to: engine.mainMixerNode, format: format)
            playerNodes.append(node)
        }

        engine.mainMixerNode.outputVolume = 0.8

        do {
            try engine.start()
        } catch {
            print("AudioEngine failed to start: \(error)")
        }
    }

    func playNote(frequency: Double, waveform: WaveformType, duration: Double = 0.45) {
        guard engine.isRunning, let format = audioFormat else { return }

        let node = playerNodes[nodeIndex % poolSize]
        nodeIndex += 1

        let sampleRate: Double = 44100
        let frameCount = AVAudioFrameCount(sampleRate * duration)

        guard let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: frameCount) else { return }
        buffer.frameLength = frameCount

        guard let channelData = buffer.floatChannelData?[0] else { return }

        let attack = 0.008
        let release = 0.12

        for i in 0..<Int(frameCount) {
            let t = Double(i) / sampleRate
            let envelope: Double
            if t < attack {
                envelope = t / attack
            } else if t > duration - release {
                envelope = max(0, (duration - t) / release)
            } else {
                envelope = 1.0
            }
            channelData[i] = Float(generateSample(t: t, frequency: frequency, waveform: waveform) * envelope * 0.45)
        }

        if !node.isPlaying { node.play() }
        node.scheduleBuffer(buffer, completionHandler: nil)
    }

    private func generateSample(t: Double, frequency: Double, waveform: WaveformType) -> Double {
        switch waveform {
        case .sine:
            return sin(2 * .pi * frequency * t)

        case .triangle:
            let phase = (frequency * t).truncatingRemainder(dividingBy: 1.0)
            return phase < 0.5 ? 4 * phase - 1 : 3 - 4 * phase

        case .square:
            let phase = (frequency * t).truncatingRemainder(dividingBy: 1.0)
            return phase < 0.5 ? 0.6 : -0.6

        case .bounce:
            // Marimba/xylophone: fundamental + decaying harmonics
            let decay = exp(-t * 6)
            return (sin(2 * .pi * frequency * t) * 0.65
                  + sin(4 * .pi * frequency * t) * 0.25 * exp(-t * 12)
                  + sin(6 * .pi * frequency * t) * 0.10 * exp(-t * 24)) * decay
        }
    }

    func stop() {
        engine.stop()
    }
}
