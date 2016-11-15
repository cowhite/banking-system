/**
 * Created by sree on 16/11/16.
 */
(function () {
    'use strict';
    angular
      .module('auth')
      .controller('SignInController', SignInController);

    function SignInController () {
      var vm = this;

      vm.username = '';
      vm.email = '';
      vm.password = '';


    }
  }
)();