const express = require('express');
const http = require('http');
const https = require('https');
const fs = require('fs');
const config = require('./config.json');
const { createProxyMiddleware } = require('http-proxy-middleware');
const proxyLib = require('./lib/index');
const proxy = new proxyLib(config.prefix, {
  localAddress: config.localAddresses ? config.localAddresses : false,
  blacklist: config.blockedHostnames ? config.blockedHostnames : false
});
const index_file = 'index.html';
const atob = str => Buffer.from(str, 'base64').toString('utf-8');

// Crear una instancia de Express
const app = express();

// Middleware para evitar que se cargue en un iframe
app.use((req, res, next) => {
  res.setHeader('X-Frame-Options', 'DENY'); // Evita que se cargue en un iframe desde otro dominio
  next();
});

app.use('/api', createProxyMiddleware({
  target: 'http://python-app:5000',
  changeOrigin: true
}));

// Middleware para manejar las solicitudes con el proxy
app.use((req, res, next) => {
  if (req.url.startsWith(config.prefix)) {
    return proxy.http(req, res);
  }

  req.pathname = req.url.split('#')[0].split('?')[0];
  req.query = {};
  req.url.split('#')[0].split('?').slice(1).join('?').split('&').forEach(query => req.query[query.split('=')[0]] = query.split('=').slice(1).join('='));

  if (req.query.url && (req.pathname == '/prox' || req.pathname == '/prox/' || req.pathname == '/session' || req.pathname == '/session/')) {
    var url = atob(req.query.url);

    if (url.startsWith('https://') || url.startsWith('http://')) url = url;
    else if (url.startsWith('//')) url = 'http:' + url;
    else url = 'http://' + url;

    return (res.writeHead(301, { location: config.prefix + proxy.proxifyRequestURL(url) }), res.end(''));
  }

  // General file server.
  const publicPath = __dirname + '/public' + req.pathname;
  const error = () => (res.statusCode = 404, res.end(fs.readFileSync(__dirname + '/lib/error.html', 'utf-8').replace('%ERR%', `Cannot ${req.method} ${req.pathname}`)));

  fs.lstat(publicPath, (err, stats) => {
    if (err) return error();

    if (stats.isDirectory()) fs.existsSync(publicPath + index_file) ? fs.createReadStream(publicPath + index_file).pipe(res) : error();
    else if (stats.isFile()) !publicPath.endsWith('/') ? fs.createReadStream(publicPath).pipe(res) : error();
    else error();
  });
});

const server = config.ssl ? https.createServer({key: fs.readFileSync('./ssl/default.key'), cert: fs.readFileSync('./ssl/default.crt')}, app) : http.createServer(app);

// Websocket proxy.
proxy.ws(server);

server.listen(process.env.PORT || config.port, () => console.log(`${config.ssl ? 'https://' : 'http://'}0.0.0.0:${config.port}`));
