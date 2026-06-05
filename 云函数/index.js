const cloud = require('wx-server-sdk')

cloud.init({
  env: cloud.DYNAMIC_CURRENT_ENV
})


const axios = require('axios')
const API_BASE_URL = 'http://1.2.3.4:8000/api'

// 云函数入口函数
exports.main = async (event, context) => {
  console.log('收到事件:', event)

  const openid = event.FromUserName
  const content = event.Content

  if (!openid || !content) {
    console.error('缺少必要参数')
    return 'success'
  }

  try {
    const response = await axios.post(
      `${API_BASE_URL}/connect`,
      { openid, content },
      { timeout: 60000 }   // 10 秒即可，因为云函数很快会返回
    )

    console.log('完整回复',response)
    const res = response.data.data.response
    console.log('收到回复:', res)

    await cloud.openapi.customerServiceMessage.send({
      touser: openid,          // 使用 FromUserName
      msgtype: 'text',
      text: {
        content: res,
      },
    })

  } catch (error) {
    console.error('调用失败:', error.message)
  }

  return 'success'  // 立即返回，不再阻塞
}