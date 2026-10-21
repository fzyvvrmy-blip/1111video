$ErrorActionPreference = 'Stop'
$audioFolder = Join-Path $PSScriptRoot 'audio'
New-Item -ItemType Directory -Path $audioFolder -Force | Out-Null
$voice = New-Object -ComObject SAPI.SpVoice
$token = New-Object -ComObject SAPI.SpObjectToken
$token.SetId('HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices\Tokens\MSTTS_V110_zhCN_KangkangM')
$voice.Voice = $token
$voice.Rate = 2
$voice.Volume = 100
$stream = New-Object -ComObject SAPI.SpFileStream
$stream.Open((Join-Path $audioFolder 'bookseller-voice-temp.wav'), 3, $false)
try {
    $voice.AudioOutputStream = $stream
    $voice.Speak('花卉鉴赏！两学分！早八精品，美育好课！看一看，挑一挑！三，二，一，上链接！') | Out-Null
} finally { $stream.Close() }
Write-Output 'Temporary synthetic narration saved.'
