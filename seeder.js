const { configDotenv } = require("dotenv");
const mongoose = require("mongoose");
const fs = require('fs');
const path = require("path");
configDotenv()


mongoose.connect(process.env.MONGO_URI).then(() => {
    fs.readFile(path.join(__dirname, 'backend.products.json'), {encoding: 'utf8'}, async (err, data) => {
        if (err) throw new Error(err)
        products = JSON.parse(data)
        products  = products.map(product => {
            if (product._id && product._id.$oid) {
                product._id = new mongoose.Types.ObjectId(product._id.$oid);
            }
            return product
        })

        const productsCollection =  mongoose.connection.collection('products')
        await productsCollection.insertMany(products)
        console.log("Seeded");
    })

    
 }).catch(e => console.log(e))

