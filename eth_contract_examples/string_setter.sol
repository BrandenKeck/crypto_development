// The most basic solidity script that can be created:
// Constructor sets string on contract creation
// Update is a publicly callable function

pragma solidity ^0.5.0;

contract string_setter {

    string public message;

    constructor(string memory init_message) public {
        message = init_message;
    }

    function update(string memory new_message) public {
        message = new_message;
    }
}
