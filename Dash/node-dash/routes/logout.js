const express = require('express');
const router = express.Router();

// Logout route
router.get('/', (req, res) => {
    req.session.destroy(err => {
        if (err) {
            console.error('Error destroying session:', err);
            return res.status(500).send('Error logging out');
        }
        res.clearCookie('connect.sid'); // clear session cookie
        res.redirect('/login');
    });
});

module.exports = router;
