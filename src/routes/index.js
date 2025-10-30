import express from 'express';
import {showLandingPage} from '../controllers/mainController.js';

const router = express.Router();

router.get('/', showLandingPage);

export default router;