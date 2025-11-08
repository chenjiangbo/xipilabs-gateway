const express = require('express');
const jwt = require('jsonwebtoken');
const cookieParser = require('cookie-parser');

const app = express();
const port = process.env.PORT || 3000;

app.use(cookieParser());

app.get('/verify', (req, res) => {
    const token = req.cookies['auth-token'];

    if (!token) {
        return res.status(401).send('Unauthorized: No token provided');
    }

    const jwtSecret = process.env.JWT_SECRET;
    if (!jwtSecret) {
        console.error('JWT_SECRET is not defined in environment variables');
        return res.status(500).send('Internal Server Error: JWT secret not configured');
    }

    try {
        const payload = jwt.verify(token, jwtSecret, {
            issuer: 'www.xipilabs.com',
            audience: 'xipilabs-products',
        });

        // 将用户信息从 payload 放入响应头，供 Nginx 捕获
        if (payload.sub) {
            res.setHeader('X-User-ID', payload.sub);
        }
        if (payload.email) {
            res.setHeader('X-User-Email', payload.email);
        }
        if (payload.phone) {
            res.setHeader('X-User-Phone', payload.phone);
        }

        res.status(200).send('OK');
    } catch (err) {
        console.log('JWT verification failed:', err.message);
        return res.status(401).send('Unauthorized: Invalid token');
    }
});

app.listen(port, () => {
    console.log(`Auth service listening on port ${port}`);
});
