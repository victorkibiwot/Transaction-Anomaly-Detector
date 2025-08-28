const express = require('express');
const bcrypt = require('bcrypt');
const { Pool } = require('pg');
const router = express.Router();

// DB connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

router.get('/', (req, res) => {
    if (req.session.user) {
        res.redirect('/dash');
    } else {
        res.redirect('/login');
    }
});

router.get('/login', (req, res) => {
    res.render('login', {error: null});
});

router.post('/logout', (req, res) => {
    req.session.destroy(() => {
        res.redirect('/login');
    });
});

router.get('/dash', (req, res) => {
    if (!req.session.user) return res.redirect('/login');
    res.render('dash', { 
        user: req.session.user, 
        transactionResult: null  // avoid undefined
    });
});


// POST: Handle login
router.post('/login', async (req, res) => {
  const { username, password } = req.body;

  try {
    const result = await pool.query('SELECT * FROM users WHERE username = $1', [username]);
    if (result.rows.length === 0) {
      return res.render('login', { error: 'Invalid username or password' });
    }

    const user = result.rows[0];
    console.log(user);
    const match = await bcrypt.compare(password, user.password_hash);

    if (!match) {
      return res.render('login', { error: 'Invalid username or password' });
    }

    // Store user session
    req.session.user = {
      id: user.user_id,
      username: user.username,
      account_balance: user.account_balance
    };

    res.redirect('/dash');
  } catch (err) {
    console.error(err);
    res.render('login', { error: 'An error occurred. Please try again.' });
  }
});


module.exports = router;
