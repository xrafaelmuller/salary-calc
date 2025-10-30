import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";
import router from "./src/routes/index.js";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "src/views"));

app.use(express.static(path.join(__dirname, "src/public")));
app.use("/", router);

app.listen(PORT, () => {
    console.log(`🌐 Server running on http://localhost:${PORT}`);
});
