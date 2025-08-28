// routes/transact.js
const express = require('express');
const router = express.Router();
const axios = require('axios');

router.post('/', async (req, res) => {
  try {
    const { amount } = req.body;

    // Ensure user is logged in
    if (!req.session.user || !req.session.user.id) {
      return res.redirect('/login');
    }

    const userId = req.session.user.id;

    const payload = {
      user_id: userId,
      amount: amount
    };

    console.log(payload);

    // Call FastAPI endpoint
    const response = await axios.post(
      'http://127.0.0.1:8000/transactions',
      payload,
      { headers: { 'Content-Type': 'application/json' } }
    );

    // Extract and send to template
    const { prediction, probability, message } = response.data;

    res.render('dash', {
      user: req.session.user,
      transactionResult: { prediction, probability, message }
    });

  } catch (err) {
    if (err.response) {
      console.error('FastAPI error:', err.response.data);

      // Check if it's the "Insufficient funds" case
      if (err.response.data.detail === 'Insufficient funds.') {
        return res.render('dash', {
          user: req.session.user,
          transactionResult: {
            prediction: null,
            probability: null,
            message: err.response.data.detail // display message
          }
        });
      }

      // Other known FastAPI error
      return res.render('dash', {
        user: req.session.user,
        transactionResult: {
          prediction: null,
          probability: null,
          message: err.response.data.detail || 'An error occurred.'
        }
      });
    }

    // Unhandled request error
    console.error('Request error:', err.message);
    res.status(500).send('Error processing transaction.');
  }
});

module.exports = router;
