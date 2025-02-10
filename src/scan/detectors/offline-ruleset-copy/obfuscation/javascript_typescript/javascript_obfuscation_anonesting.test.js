
(function() {
    let a = 1;
    (function() {
        let x = 5
        (function() {
            console.log('Nested anonymous');
        })();
    })();
})();

let validName = function() {};
let validFunc = () => {};

let obj2 = {
    method() {
        return "test";
    }
};