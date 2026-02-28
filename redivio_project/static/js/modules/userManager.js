export const userModule = {
    state: {
        users: [],
        currentUser: null
    },
    methods: {
        async fetchUsers() {
            // كود جلب المستخدمين من السيرفر
        },
        addUser(user) {
            this.users.push(user);
        }
    }
};