/**
 * wechaty 网关：用一个微信小号登录，把收到的 HTTP 推送转发到指定群。
 *
 * 接口：
 *   POST /push  { "group": "群名称", "text": "内容" }  -> 转发到该群
 *   GET  /health                                      -> { ready: bool }
 *
 * 环境变量：
 *   PORT                 监听端口（默认 8788）
 *   WECHAT_GROUP_TOPIC   默认群名（push 未带 group 时用）
 *   WECHATY_PUPPET       puppet 类型（默认 wechaty-puppet-wechat 免费 web 协议）
 *
 * ⚠️ 非官方自动化，有封号风险，请用小号。
 */
const http = require('http')
const { WechatyBuilder } = require('wechaty')
const qrcodeTerminal = require('qrcode-terminal')

const PORT = parseInt(process.env.PORT || '8788', 10)
const DEFAULT_GROUP = process.env.WECHAT_GROUP_TOPIC || ''
const PUPPET = process.env.WECHATY_PUPPET || 'wechaty-puppet-wechat'

const bot = WechatyBuilder.build({ name: 'digest-bot', puppet: PUPPET })
let ready = false

bot.on('scan', (qrcodeUrl, status) => {
  // status 2 = 待扫码
  if (status === 2 || status === 0) {
    console.log('\n用【微信小号】扫码登录（切勿用主号）：\n')
    qrcodeTerminal.generate(qrcodeUrl, { small: true })
    console.log('\n如上二维码扫不出，可用链接生成：https://wechaty.js.org/qrcode/' +
      encodeURIComponent(qrcodeUrl) + '\n')
  }
})
bot.on('login', user => { ready = true; console.log('✅ 已登录:', user.name()) })
bot.on('logout', user => { ready = false; console.log('已登出:', user && user.name()) })
bot.on('error', err => console.error('wechaty error:', err && err.message))

async function sendToGroup(topic, text) {
  const room = await bot.Room.find({ topic })
  if (!room) throw new Error('找不到群（群名称需完全一致）: ' + topic)
  await room.say(text)
}

const server = http.createServer((req, res) => {
  const json = (code, obj) => {
    res.writeHead(code, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify(obj))
  }
  if (req.method === 'GET' && req.url === '/health') {
    return json(200, { ready })
  }
  if (req.method === 'POST' && req.url === '/push') {
    let body = ''
    req.on('data', c => (body += c))
    req.on('end', async () => {
      try {
        const { group, text } = JSON.parse(body || '{}')
        if (!ready) throw new Error('尚未登录，请先扫码')
        if (!text) throw new Error('text 为空')
        await sendToGroup(group || DEFAULT_GROUP, text)
        json(200, { ok: true })
      } catch (e) {
        console.error('push 失败:', e.message)
        json(500, { ok: false, error: String(e.message || e) })
      }
    })
    return
  }
  json(404, { ok: false, error: 'not found' })
})

server.listen(PORT, () => console.log('wechaty 网关已启动 :' + PORT))
bot.start().catch(e => { console.error('启动失败:', e); process.exit(1) })
