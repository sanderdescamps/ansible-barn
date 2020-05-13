db.createUser(
    {
        user: "mongo-user",
        pwd: "mDFKMDFJAMZLFNQMDSLFIHADFANMDFJAlEFjkdfjoqjdf",
        roles: [
            {
                role: "readWrite",
                db: "inventory"
            }
        ]
    }
);