const express = require('express');
const session = require('express-session');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Session setup
app.use(
  session({
    secret: process.env.SESSION_SECRET || 'supersecretkey',
    resave: false,
    saveUninitialized: false,
  })
);

// Routes
const loginRoutes = require('./routes/login');
app.use('/', loginRoutes);

const logoutRouter = require('./routes/logout');
app.use('/logout', logoutRouter);

const transactRoute = require('./routes/transact');
app.use('/transact', transactRoute);


// Start server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
