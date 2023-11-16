"use strict";

import file from "./product_data.json" assert {type: 'json' }

const app = document.getElementById('root');
let num = Math.floor(Math.random() * 5);
for (let i = 0; i < num; i++) {
    const imagen = document.createElement('img');
    let random_num = Math.floor(Math.random() * file.length);
const source = file[random_num]["des_filename"];
app.appendChild(imagen);
imagen.setAttribute("src", source);
  }
console.log(file.length);
