angular.module(
  'FrontendApp',
  [
    'ngResource'
  ]
)
.config(
  [
    '$httpProvider',
    '$resourceProvider',
    '$interpolateProvider',
    function(
      $httpProvider,
      $resourceProvider,
      $interpolateProvider
    ) {
      $httpProvider.defaults.xsrfCookieName = 'csrftoken';
      $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
      $resourceProvider.defaults.stripTrailingSlashes = false;
      $interpolateProvider.startSymbol('{$');
      $interpolateProvider.endSymbol('$}');
    }
  ]
)
.factory(
  'Presentation',
  [
    '$resource',
    function(
      $resource
    ) {
      return $resource(
        '/api/presentations/:id/',
        {
          id: '@id'
        }
      );
    }
  ]
)
.factory(
  'Synchronization',
  [
    '$resource',
    function(
      $resource
    ) {
      return $resource(
        '/api/synchronizations/:id/',
        {
          id: '@id'
        }
      );
    }
  ]
)
.factory(
  'Repository',
  [
    '$resource',
    function(
      $resource
    ) {
      return $resource(
        '/api/repositories/:id/',
        {
          id: '@id'
        },
        {
          activate: {
            method: 'ACTIVATE',
            url: '/api/repositories/:id/state/'
          },
          deactivate: {
            method: 'DEACTIVATE',
            url: '/api/repositories/:id/state/'
          }
        }
      );
    }
  ]
)
.controller(
  'PresentationsController',
  [
    'Presentation',
    '$scope',
    function(
      Presentation,
      $scope
    ) {
      $scope.presentations = Presentation.query();
    }
  ]
)
.controller(
  'RepositoriesController',
  [
    'Repository',
    'Synchronization',
    '$scope',
    '$timeout',
    function(
      Repository,
      Synchronization,
      $scope,
      $timeout
    ) {
      var stateMap = {
        'PENDING': function(sync) {
          $scope.syncActive = true;
        },
        'PROGRESS': function(sync) {
          $scope.syncProgress = sync.result.total / 100 * sync.result.current;
        },
        'SUCCESS': function(sync) {
          $scope.repositories = Repository.query();
          $scope.syncActive = false;
        },
      };
      $scope.syncActive = false;
      $scope.repositories = Repository.query();
      $scope.syncGithub = function() {
        $scope.sync = new Synchronization();
        $scope.sync.$save(function() {
          (function tick() {
            $scope.sync.$get(function(){
              if ($scope.sync.state !== 'SUCCESS') {
                $timeout(tick, 2000);
              }
              stateMap[$scope.sync.state]($scope.sync);
            });
          })();
        });
      };
      $scope.toggleRepository = function(repo) {
        repo._working = true;
        var result;
        if (repo.state != 'active') {
          result = Repository.activate({id: repo.id});
        } else {
          result = Repository.deactivate({id: repo.id});
        }
        result.$promise.then(function(data) {
          angular.extend(repo, data);
        repo._working = false;
        });
      }
    }
  ]
);
