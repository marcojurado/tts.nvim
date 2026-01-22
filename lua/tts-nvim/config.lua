M = {}

M.opts = {
    voice = "en-GB-SoniaNeural", -- Deprecated, use 'language' instead
    language = "en",
    speed = 1.0,
    remove_syntax = false, -- Enable syntax removal for supported filetypes
    syntax_removal_method = "pandoc", -- "simple" (pattern-based) or "pandoc"
    backend = "edge", -- TTS backend: "edge", "piper", or "openai"

    -- Language to voice mappings per backend
    languages_to_voice = {
        -- Edge TTS voices (400+ available)
        edge = {
            ["en"] = "en-GB-SoniaNeural",
            ["pt"] = "pt-BR-AntonioNeural",
            ["es"] = "es-ES-ElviraNeural",
            ["fr"] = "fr-FR-DeniseNeural",
            ["de"] = "de-DE-KatjaNeural",
            ["it"] = "it-IT-ElsaNeural",
            ["ja"] = "ja-JP-NanamiNeural",
            ["zh"] = "zh-CN-XiaoxiaoNeural",
        },
        -- Piper models (local neural TTS)
        piper = {
            ["en"] = "en_US-lessac-medium",
            ["pt"] = "pt_BR-faber-medium",
            ["es"] = "es_ES-sharvard-medium",
            ["fr"] = "fr_FR-siwis-medium",
            ["de"] = "de_DE-thorsten-medium",
            ["it"] = "it_IT-riccardo-x_low",
            ["ja"] = "ja_JP-haruka-medium",
            ["zh"] = "zh_CN-huayan-medium",
        },
        -- OpenAI TTS uses the same voice for all languages
        -- Set the voice in openai.voice option below
    },

    -- Piper configuration
    piper_model = "en_US-lessac-medium", -- Piper model to use
    -- Optional: override the command used to run piper CLI actions (string).
    -- If nil the plugin will use: `python3 -m piper.download_voices --download-dir ... <model>`
    -- Example: piper = { command = "piper download_voices" }
    piper = {
        command = nil,
    },

    -- Edge configuration (present for parity; edge backend currently uses Python API)
    -- Example: edge = { command = "edge-tts" }  (not used by default API implementation)
    edge = {
        command = nil,
    },

    -- Player configuration: override the base player command string.
    -- The plugin will split this string and append backend-specific stdin args.
    -- Example: player = { command = "ffplay" } or player = { command = "mpv --no-terminal" }
    player = {
        command = nil,
    },

    -- OpenAI TTS configuration
    -- Note: API key must be set via OPENAI_API_KEY environment variable
    openai = {
        voice = "alloy", -- Available: alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, shimmer
        model = "tts-1", -- "tts-1" or "tts-1-hd"
    },
}

M.setup_config = function(opts)
    opts = opts or {}
    if opts.voice ~= nil then
        print("Warning: 'voice' option is deprecated. Please use 'language' option instead.")
    end
    M.opts = vim.tbl_deep_extend("force", M.opts, opts)
end

return M
