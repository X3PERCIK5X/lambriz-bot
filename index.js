import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { Telegraf, Markup } from "telegraf";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ENV_PATH = path.join(__dirname, "config.env");

function loadEnvFile(filePath) {
  if (!fs.existsSync(filePath)) return;
  const lines = fs.readFileSync(filePath, "utf-8").split("\n");
  for (const raw of lines) {
    const line = raw.trim();
    if (!line || line.startsWith("#") || !line.includes("=")) continue;
    const [key, ...rest] = line.split("=");
    const value = rest.join("=").trim().replace(/^"|"$/g, "").replace(/^'|'$/g, "");
    if (process.env[key] === undefined) {
      process.env[key] = value;
    }
  }
}

loadEnvFile(ENV_PATH);

const config = {
  botToken: process.env.BOT_TOKEN,
  webAppUrl: process.env.WEBAPP_URL,
  logoPath: process.env.LOGO_PATH || "./assets/logo.png",
  welcomeText:
    process.env.WELCOME_TEXT ||
    "Ламбриз — поставка оборудования и изделий из нержавейки. Откройте каталог и оформите заявку прямо в Mini App."
};

if (!config.botToken) {
  console.error("BOT_TOKEN не задан. Укажите его в config.env рядом с index.js");
  process.exit(1);
}

const bot = new Telegraf(config.botToken);

bot.start(async (ctx) => {
  const logoFullPath = path.isAbsolute(config.logoPath)
    ? config.logoPath
    : path.join(__dirname, config.logoPath);

  if (fs.existsSync(logoFullPath)) {
    await ctx.replyWithPhoto({ source: logoFullPath });
  }

  const buttons = [];
  if (config.webAppUrl) {
    buttons.push(Markup.button.webApp("Каталог", config.webAppUrl));
  }

  await ctx.reply(
    config.welcomeText,
    buttons.length ? Markup.inlineKeyboard([buttons]) : undefined
  );
});

bot.launch().then(() => {
  console.log("Lambriz bot started.");
});

process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
