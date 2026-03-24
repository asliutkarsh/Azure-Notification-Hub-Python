import express from 'express'
import cors from 'cors'
import config from './config.js'
import routes from './routes.js'

const app = express()

app.use(cors({ origin: '*' }))
app.use(express.json())

app.use('/api', routes)

app.listen(config.server.port, () => {
  console.log(`Backend running on http://localhost:${config.server.port}`)
})
