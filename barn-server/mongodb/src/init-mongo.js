db.createUser(
    {
      user: "testuser",
      pwd: "test",
      roles: [ "readWrite", "dbAdmin" ]
    }
)