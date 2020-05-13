db.createUser(
    {
        user: "mongo-user",
        pwd: "mDFKMDFJAMZLFNQMDSLFIHADFANMDFJAlEFjkdfjoqjùdf",
        roles: [
            {
                role: "readWrite",
                db: "inventory"
            }
        ]
    }
);