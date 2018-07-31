<?php
 
namespace Drupal\avoindata_guide\Plugin\Derivative;
 
use Drupal\Component\Plugin\Derivative\DeriverBase;
use Drupal\Core\Plugin\Discovery\ContainerDeriverInterface;
use Drupal\Core\Entity\EntityTypeManagerInterface;
use Symfony\Component\DependencyInjection\ContainerInterface;
 
/**
 * This file is based on this guide:
 * https://www.webomelette.com/dynamic-menu-links-drupal-8-plugin-derivatives
 * Derivative class that provides the menu links for the Products.
 */
class GuideMenuLink extends DeriverBase implements ContainerDeriverInterface {
 
   /**
   * @var EntityTypeManagerInterface $entityTypeManager.
   */
  protected $entityTypeManager;
 
  /**
   * Creates a GuideMenuLink instance.
   *
   * @param $base_plugin_id
   * @param EntityTypeManagerInterface $entity_type_manager
   */
  public function __construct($base_plugin_id, EntityTypeManagerInterface $entity_type_manager) {
    $this->entityTypeManager = $entity_type_manager;
  }
 
  /**
   * {@inheritdoc}
   */
  public static function create(ContainerInterface $container, $base_plugin_id) {
    return new static(
      $base_plugin_id,
      $container->get('entity_type.manager')
    );
  }
 
  /**
   * {@inheritdoc}
   */
  public function getDerivativeDefinitions($base_plugin_definition) {
    $links = [];
 
    // We assume we don't have too many...
    $guide_links = $this->entityTypeManager->getStorage('avoindata_guide_page')->loadMultiple();
    foreach ($guide_links as $id => $guide_link) {
      $guide_links[$id] = [
        'title' => $guide_link->title(),
        'route_name' => $guide_link->toUrl()->getRouteName(),
        'route_parameters' => ['guide_link' => $product->id()]
      ] + $base_plugin_definition;
    }
 
    return $guide_links;
  }
}